from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, backref
from datetime import datetime


class ServerDB:
    Base = declarative_base()

    class User(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        username = Column(String, unique=True)
        last_connection_time = Column(DateTime)
        sent = Column(Integer)
        received = Column(Integer)

        def __init__(self, username):
            self.username = username
            self.last_connection_time = datetime.now()
            self.sent = 0
            self.received = 0

        @property
        def ru_dt(self):
            return ServerDB.get_ru_dt(self.last_connection_time)

    class Connection(Base):
        __tablename__ = 'connections'
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('users.id'), unique=True)
        user = relationship('User', backref=backref("connections"), lazy='joined')
        ip = Column(String)
        port = Column(Integer)
        connection_time = Column(DateTime)

        def __init__(self, user_id, ip, port, connection_time):
            self.user_id = user_id
            self.ip = ip
            self.port = port
            self.connection_time = connection_time

        @property
        def ru_dt(self):
            return ServerDB.get_ru_dt(self.connection_time)

    class Authorization(Base):
        __tablename__ = 'authorizations'
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('users.id'))
        user = relationship('User', backref=backref("authorizations"), lazy='joined')
        ip = Column(String)
        port = Column(Integer)
        connection_time = Column(DateTime)

        def __init__(self, user_id, ip, port, connection_time):
            self.user_id = user_id
            self.ip = ip
            self.port = port
            self.connection_time = connection_time

        @property
        def ru_dt(self):
            return ServerDB.get_ru_dt(self.connection_time)

    class Contact(Base):
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('users.id'))
        user = relationship('User', foreign_keys=[user_id], backref=backref("contacts"))
        contact_user_id = Column(Integer, ForeignKey('users.id'))
        contact_user = relationship('User', foreign_keys=[contact_user_id], lazy='joined')

        def __init__(self, user_id, contact_user_id):
            self.user_id = user_id
            self.contact_user_id = contact_user_id

    def __init__(self, db_path):
        uri = 'sqlite:///{}'.format(db_path)
        self.engine = create_engine(uri, echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})
        self.Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.Connection).delete()
        self.session.commit()

    def user_login(self, username, ip, port):
        user = self.get_user_by_name(username)
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

    def process_message(self, sender_name, recipient_name):
        sender = self.get_user_by_name(sender_name)
        recipient = self.get_user_by_name(recipient_name)
        sender.sent += 1
        recipient.received += 1
        self.session.commit()

    def get_users(self):
        return self.session.query(self.User).all()

    def get_connections(self):
        return self.session.query(self.Connection).all()

    def get_authorizations(self, username=None):
        query = self.session.query(self.Authorization)
        if username:
            query = query.filter(self.Authorization.user.has(username=username))
        return query.all()

    def add_contact(self, user_name, contact_user_name):
        user = self.get_user_by_name(user_name)
        contact_user = self.get_user_by_name(contact_user_name)

        if (not contact_user) or self.session.query(self.Contact).\
                filter_by(user_id=user.id, contact_user_id=contact_user.id).count():
            return

        contact = self.Contact(user.id, contact_user.id)
        self.session.add(contact)
        self.session.commit()

    def del_contact(self, user_name, contact_user_name):

        contact = self.session.query(self.Contact).filter(
            self.Contact.user.has(username=user_name),
            self.Contact.contact_user.has(username=contact_user_name)
        ).first()

        if contact:
            self.session.delete(contact)
            self.session.commit()

    def get_user_by_name(self, username):
        return self.session.query(self.User).filter_by(username=username).first()

    @staticmethod
    def get_ru_dt(dt_field):
        dt = f'{dt_field}'.split(' ')
        d = dt[0].split('-')
        t = dt[1][:5]
        return f'{t} {d[2]}.{d[1]}.{d[0]}'


if __name__ == '__main__':
    db = ServerDB('test_server.sqlite3')
    db.user_login('user1', '192.168.1.4', 8888)
    db.user_login('user2', '192.168.1.5', 7777)
    db.user_login('user3', '192.168.1.6', 4564)

    db.user_logout('user1')

    print('\n====== all users =======')
    for db_user in db.get_users():
        print(db_user.username, db_user.last_connection_time)

    print('\n====== connection users =======')
    for conn in db.get_connections():
        print(conn.ip, conn.user.username)

    print('\n====== authorizations for all =======')
    for authorization in db.get_authorizations():
        print(authorization.connection_time, authorization.user.username)

    print('\n====== authorizations for user1 =======')
    for authorization in db.get_authorizations('user1'):
        print(authorization.connection_time, authorization.user.username)

    print('\n====== contacts for user1 =======')
    db.add_contact('user1', 'user2')
    db.add_contact('user1', 'user3')
    user1 = db.get_user_by_name('user1')
    for cont in user1.contacts:
        print(cont.contact_user.username)

    print('\n====== contacts for user1 after deleting =======')
    db.del_contact('user1', 'user2')
    for cont in user1.contacts:
        print(cont.contact_user.username)

