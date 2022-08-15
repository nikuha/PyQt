from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


class ClientDB:
    Base = declarative_base()

    class User(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        username = Column(String, unique=True)

        def __init__(self, username):
            self.username = username

    class Message(Base):
        __tablename__ = 'messages'
        id = Column(Integer, primary_key=True)
        sender_id = Column(Integer, ForeignKey('users.id'))
        sender = relationship('User', foreign_keys=[sender_id], lazy='joined')
        recipient_id = Column(Integer, ForeignKey('users.id'))
        recipient = relationship('User', foreign_keys=[recipient_id], lazy='joined')
        message = Column(Text)
        created_dt = Column(DateTime)

        def __init__(self, sender_id, recipient_id, message):
            self.sender_id = sender_id
            self.recipient_id = recipient_id
            self.message = message
            self.created_dt = datetime.now()

    class Contact(Base):
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        contact_user_id = Column(Integer, ForeignKey('users.id'))
        contact_user = relationship('User', foreign_keys=[contact_user_id], lazy='joined')

        def __init__(self, contact_user_id):
            self.contact_user_id = contact_user_id

    def __init__(self, db_path):
        uri = f'sqlite:///{db_path}'
        self.engine = create_engine(uri, echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})
        self.Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.Contact).delete()
        self.session.commit()

    def add_contact(self, contact_user_name):
        contact_user = self.get_user_by_name(contact_user_name)

        if (not contact_user) or self.session.query(self.Contact).\
                filter_by(contact_user_id=contact_user.id).count():
            return

        contact = self.Contact(contact_user.id)
        self.session.add(contact)
        self.session.commit()

    def del_contact(self, contact_user_name):
        contact = self.session.query(self.Contact).filter(
            self.Contact.contact_user.has(username=contact_user_name)
        ).first()

        if contact:
            self.session.delete(contact)
            self.session.commit()

    def add_users(self, users_list):
        for username in users_list:
            user = self.get_user_by_name(username)
            if not user:
                user = self.User(username)
                self.session.add(user)
        self.session.commit()

    def save_message(self, sender_username, recipient_username, message):
        sender = self.get_user_by_name(sender_username)
        recipient = self.get_user_by_name(recipient_username)
        if sender and recipient:
            message_record = self.Message(sender.id, recipient.id, message)
            self.session.add(message_record)
            self.session.commit()

    def get_contacts(self):
        return self.session.query(self.Contact).all()

    def get_users(self):
        return self.session.query(self.User).all()

    def get_messages(self, sender_id=None, recipient_id=None):
        query = self.session.query(self.Message)
        if sender_id:
            query = query.filter_by(sender_id=sender_id)
        if recipient_id:
            query = query.filter_by(recipient_id=recipient_id)
        return query.all()

    def get_user_by_name(self, username):
        return self.session.query(self.User).filter_by(username=username).first()


if __name__ == '__main__':
    db = ClientDB('test_client.sqlite3')

    db.add_users(['test1', 'test2', 'test3', 'test4', 'test5'])

    print('\n====== all users =======')
    for user_item in db.get_users():
        print(f'{user_item.username}')

    for i in ['test3', 'test4', 'test5', 'test4']:
        db.add_contact(i)

    print('\n====== contacts =======')
    for contact_item in db.get_contacts():
        print(f'{contact_item.contact_user.username}')

    db.del_contact('test5')

    print('\n====== contacts after deleting =======')
    for contact_item in db.get_contacts():
        print(f'{contact_item.contact_user.username}')

    db.save_message('test1', 'test2', f'тестовое сообщение1')
    db.save_message('test2', 'test1', f'тестовое сообщение2')

    print('\n====== messages =======')
    for message_item in db.get_messages():
        print(f'{message_item.sender.username} -> {message_item.recipient.username}: {message_item.message}')
