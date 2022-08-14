from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, backref
from datetime import datetime
from os import path

db_path = path.join(path.dirname(__file__), 'server.sqlite3')
DB_URI = 'sqlite:///{}'.format(db_path)


class ServerDB:
    Base = declarative_base()

    class User(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        username = Column(String, unique=True)
        last_connection_time = Column(DateTime)

        def __init__(self, username):
            self.username = username
            self.last_connection_time = datetime.now()

    class Connection(Base):
        __tablename__ = 'connections'
        id = Column(Integer, primary_key=True)
        user_id = Column(String, ForeignKey('users.id'), unique=True)
        user = relationship('User', backref=backref("connections", uselist=False), lazy='joined')
        ip = Column(String)
        port = Column(Integer)
        connection_time = Column(DateTime)

        def __init__(self, user_id, ip, port, connection_time):
            self.user_id = user_id
            self.ip = ip
            self.port = port
            self.connection_time = connection_time

    class Authorization(Base):
        __tablename__ = 'authorizations'
        id = Column(Integer, primary_key=True)
        user_id = Column(String, ForeignKey('users.id'))
        user = relationship('User', backref=backref("authorizations"), lazy='joined')
        ip = Column(String)
        port = Column(Integer)
        connection_time = Column(DateTime)

        def __init__(self, user_id, ip, port, connection_time):
            self.user_id = user_id
            self.ip = ip
            self.port = port
            self.connection_time = connection_time

    def __init__(self):
        self.engine = create_engine(DB_URI, echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})
        self.Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.Connection).delete()
        self.session.commit()

    def user_login(self, username, ip, port):
        user = self.session.query(self.User).filter_by(username=username).first()
        if user:
            user.last_connection_time = datetime.now()
        else:
            user = self.User(username)
            self.session.add(user)
            self.session.commit()

        connection = self.Connection(user.id, ip, port, datetime.now())
        self.session.add(connection)

        history = self.Authorization(user.id, ip, port, datetime.now())
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        # не работает в один запрос (почему? all() с таким фильтром работает)
        # self.session.query(self.Online).filter(self.Online.user.has(username=username)).delete()

        # так работает, но получается тоже 2 запроса
        connection = self.session.query(self.Connection).filter(self.Connection.user.has(username=username)).first()
        self.session.delete(connection)

        # user = self.session.query(self.User).filter_by(username=username).first()
        # self.session.query(self.Online).filter_by(user_id=user.id).delete()

        self.session.commit()

    def get_users(self):
        return self.session.query(self.User.username, self.User.last_connection_time).all()

    def get_connections(self):
        return self.session.query(self.Connection).all()

    def get_authorizations(self, username=None):
        query = self.session.query(self.Authorization)
        if username:
            query = query.filter(self.Authorization.user.has(username=username))
        return query.all()


if __name__ == '__main__':
    db = ServerDB()
    db.user_login('user1', '192.168.1.4', 8888)
    db.user_login('user2', '192.168.1.5', 7777)
    db.user_login('user3', '192.168.1.6', 4564)

    db.user_logout('user1')

    print('\n====== all users =======')
    for db_user in db.get_users():
        print(db_user)

    print('\n====== connection users =======')
    for conn in db.get_connections():
        print(conn.ip, conn.user.username)

    print('\n====== authorizations for all =======')
    for authorization in db.get_authorizations():
        print(authorization.connection_time, authorization.user.username)

    print('\n====== authorizations for user1 =======')
    for authorization in db.get_authorizations('user1'):
        print(authorization.connection_time, authorization.user.username)

