import os.path
import sys
import json
import argparse
import threading
import time

from PyQt5.QtCore import pyqtSignal, QObject, QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

import common.settings as settings
from client.qt.login_dialog import LoginDialog
from client.qt.main_window import MainWindow
from common.tcp_socket import TCPSocket
from common.meta import ClientVerifier
from common.descriptors import Port, Address
from client.client_db import ClientDB
from logs.settings.socket_logger import SocketLogger


class MsgClient(TCPSocket, QObject):
    port = Port()
    address = Address()
    lost_connection_signal = pyqtSignal()
    load_data_signal = pyqtSignal(list, list)
    fill_chat_signal = pyqtSignal(str, list, bool)
    status_message_signal = pyqtSignal(str, bool)
    unlock_message_components_signal = pyqtSignal()

    def __init__(self):
        TCPSocket.__init__(self)
        QObject.__init__(self)

        socket_logger = SocketLogger(settings.CLIENT_LOGGER_NAME)
        self.logger = socket_logger.logger

        self.db = None
        self.user = {settings.REQUEST_ACCOUNT_NAME: None}
        self.main_window = None

        self.to_server_messages = []
        self.sending_wait_flag = None
        self.receiving_stop_flag = False
        self.users_loaded_flag = False

    @classmethod
    def connect_from_args(cls):
        parser = argparse.ArgumentParser()
        parser.add_argument('port', default=settings.DEFAULT_PORT, type=int, nargs='?')
        parser.add_argument('address', default=settings.DEFAULT_IP_ADDRESS, nargs='?')
        parser.add_argument('-n', default='', nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        address = namespace.address
        port = namespace.port
        account_name = namespace.n

        sock = cls()
        sock.connect(address, port, account_name)
        return sock

    def connect(self, address, port, account_name=None):
        try:
            self.port = port
        except TypeError as e:
            self.logger.critical(e)
            sys.exit(1)
        try:
            self.sock.connect((address, port))
            self.user[settings.REQUEST_ACCOUNT_NAME] = account_name
            self.logger.info(f'Подключились к серверу {address}:{port}')
        except ConnectionRefusedError:
            self.logger.critical(f'Не удалось подключиться к серверу {address}:{port}')
            sys.exit(1)

    @property
    def account_name(self):
        return self.user[settings.REQUEST_ACCOUNT_NAME]

    def mainloop(self):

        client_app = QApplication(sys.argv)

        if not self.user[settings.REQUEST_ACCOUNT_NAME]:
            login_dialog = LoginDialog()
            client_app.exec_()

            if login_dialog.ok_pressed:
                self.user[settings.REQUEST_ACCOUNT_NAME] = login_dialog.client_name.text()
                del login_dialog
            else:
                exit(0)

        self._init_db()

        sender = threading.Thread(target=self._sending_server_messages)
        sender.daemon = True
        sender.start()

        recipient = threading.Thread(target=self._receiving_server_messages)
        recipient.daemon = True
        recipient.start()

        self.main_window = MainWindow(self._add_contact_request, self._del_contact_request,
                                      self._load_user_chat, self._create_message)
        self.main_window.make_connection({
            'lost_connection_signal': self.lost_connection_signal,
            'load_data_signal': self.load_data_signal,
            'fill_chat_signal': self.fill_chat_signal,
            'status_message_signal': self.status_message_signal,
            'unlock_message_components_signal': self.unlock_message_components_signal
        })

        self._send_presence()
        self._users_request()
        self._contacts_request()

        # автоматическое обновление списка доступных пользователей
        # timer = QTimer()
        # timer.timeout.connect(self._users_request)
        # timer.start(10000)

        client_app.exec_()

    def _init_db(self):
        filename = f'client_{self.account_name}.sqlite3'
        self.db = ClientDB(os.path.join(os.getcwd(), 'client', filename))

    def _send_presence(self):
        request = self._action_request(settings.ACTION_PRESENCE)
        self.to_server_messages.append(request)

    def _sending_server_messages(self):
        while True:
            time.sleep(0.5)
            if (not self.sending_wait_flag) and self.to_server_messages:
                message = self.to_server_messages.pop(0)
                try:
                    self.send_message(self.sock, message)
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    self._lost_connection()
                else:
                    if settings.REQUEST_ACTION in message:
                        self.sending_wait_flag = message[settings.REQUEST_ACTION]

    def _receiving_server_messages(self):
        while True:
            time.sleep(0.2)
            if not self.receiving_stop_flag:
                if response := self._get_message_response():
                    self.logger.info(response)

    def _get_message_response(self):
        try:
            message = self.get_message(self.sock)

            if settings.REQUEST_ACTION not in message:
                raise ValueError(settings.REQUEST_ACTION)

            # print(f'={message[settings.REQUEST_ACTION]}')
            if self.sending_wait_flag == message[settings.REQUEST_ACTION]:
                self.sending_wait_flag = None

            if message[settings.REQUEST_ACTION] == settings.ACTION_RESPONSE:
                if settings.REQUEST_DATA not in message:
                    raise ValueError(settings.REQUEST_DATA)
                return self._get_response(message[settings.REQUEST_DATA])

            elif message[settings.REQUEST_ACTION] == settings.ACTION_PRESENCE:
                self._clear_status_message()
                return f'{self.account_name} Online'

            elif message[settings.REQUEST_ACTION] == settings.ACTION_P2P_MESSAGE:
                if settings.REQUEST_DATA not in message:
                    raise ValueError(settings.REQUEST_DATA)
                return self._get_p2p_message(message[settings.REQUEST_DATA])

            elif message[settings.REQUEST_ACTION] == settings.ACTION_GET_USERS:
                if settings.REQUEST_DATA not in message:
                    raise ValueError(settings.REQUEST_DATA)
                return self._get_users(message[settings.REQUEST_DATA])

            elif message[settings.REQUEST_ACTION] == settings.ACTION_GET_CONTACTS:
                if settings.REQUEST_DATA not in message:
                    raise ValueError(settings.REQUEST_DATA)
                return self._get_contacts(message[settings.REQUEST_DATA])

            elif message[settings.REQUEST_ACTION] == settings.ACTION_ADD_CONTACT:
                if settings.REQUEST_DATA not in message:
                    raise ValueError(settings.REQUEST_DATA)
                if settings.REQUEST_USERNAME not in message[settings.REQUEST_DATA]:
                    raise ValueError(settings.REQUEST_USERNAME)
                return self._proc_add_contact(message[settings.REQUEST_DATA][settings.REQUEST_USERNAME])

            elif message[settings.REQUEST_ACTION] == settings.ACTION_DEL_CONTACT:
                if settings.REQUEST_DATA not in message:
                    raise ValueError(settings.REQUEST_DATA)
                if settings.REQUEST_USERNAME not in message[settings.REQUEST_DATA]:
                    raise ValueError(settings.REQUEST_USERNAME)
                return self._proc_del_contact(message[settings.REQUEST_DATA][settings.REQUEST_USERNAME])

            raise ValueError
        except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError):
            self._lost_connection()
        except json.JSONDecodeError:
            return None
        except ValueError as e:
            return f'Неверный ответ сервера! {e}'

    def _action_request(self, action, data=None):
        return self.compose_action_request(action, data=data)

    @staticmethod
    def _get_response(data):
        try:
            if settings.RESPONSE_STATUS not in data:
                raise ValueError
            message_to_client = f'Status: {data[settings.RESPONSE_STATUS]}'
            if settings.RESPONSE_MESSAGE in data:
                message_to_client += f', {data[settings.RESPONSE_MESSAGE]}'
            return message_to_client
        except (ValueError, json.JSONDecodeError):
            return 'Неизвестный статус ответа сервера!'

    def _create_message(self, username, text):
        request = self._action_request(settings.ACTION_P2P_MESSAGE, data={
            settings.REQUEST_RECIPIENT: username,
            settings.REQUEST_MESSAGE: text
        })
        self.to_server_messages.append(request)

    def _get_p2p_message(self, data):
        try:
            if settings.REQUEST_STATUS in data:
                if data[settings.REQUEST_STATUS] == 200:
                    self.db.save_message(self.account_name,
                                         data[settings.REQUEST_RECIPIENT],
                                         data[settings.REQUEST_MESSAGE])
                    self._load_user_chat(data[settings.REQUEST_RECIPIENT], True)
                    self._clear_status_message()
                elif data[settings.REQUEST_STATUS] == 400:
                    self.status_message_signal.emit(f'Ошибка отправки: {data[settings.REQUEST_MESSAGE]}', True)
                self.unlock_message_components_signal.emit()
            else:
                if not (settings.RESPONSE_MESSAGE in data and settings.REQUEST_SENDER in data):
                    raise ValueError
                sender_username = data[settings.REQUEST_SENDER]
                user = self.db.get_user_by_name(sender_username)
                if not user:
                    self.db.add_users([sender_username])

                self.db.save_message(sender_username,
                                     self.account_name,
                                     data[settings.REQUEST_MESSAGE])

                self._load_user_chat(sender_username, True)
            return None
        except (ValueError, json.JSONDecodeError):
            return 'Неизвестный статус ответа сервера!'

    def _get_users(self, data):
        try:
            if not (settings.REQUEST_USERS in data):
                raise ValueError
        except (ValueError, json.JSONDecodeError):
            return 'Неизвестный статус ответа сервера!'
        else:
            self.db.add_users(data[settings.REQUEST_USERS])
            # if self.users_loaded_flag:
            #     users = [user.username for user in self.db.get_users(self.account_name)]
            #     self.load_data_signal.emit([None], sorted(users))
            # self.users_loaded_flag = True
            return None

    def _get_contacts(self, data):
        try:
            if not (settings.REQUEST_CONTACTS in data):
                raise ValueError
        except (ValueError, json.JSONDecodeError):
            return 'Неизвестный статус ответа сервера!'
        else:
            for contact in data[settings.REQUEST_CONTACTS]:
                self.db.add_contact(contact)
            self._update_window_contacts(data[settings.REQUEST_CONTACTS])
            return None

    def _update_window_contacts(self, contacts=None):
        if not contacts:
            contacts = [contact.contact_user.username for contact in self.db.get_contacts()]
        contacts.sort()
        users = [user.username for user in self.db.get_users(self.account_name)]

        self.load_data_signal.emit(contacts, sorted(users))

    def _add_contact_request(self, username):
        request = self.compose_action_request(settings.ACTION_ADD_CONTACT, data={
            settings.REQUEST_USERNAME: username
        })
        self.to_server_messages.append(request)

    def _proc_add_contact(self, username):
        self.db.add_contact(username)
        self._update_window_contacts()
        self._clear_status_message()

    def _del_contact_request(self, username):
        request = self.compose_action_request(settings.ACTION_DEL_CONTACT, data={
            settings.REQUEST_USERNAME: username
        })
        self.to_server_messages.append(request)

    def _proc_del_contact(self, username):
        self.db.del_contact(username)
        self._update_window_contacts()
        self._clear_status_message()

    def _load_user_chat(self, username, clear_field):
        messages = []
        for message_item in self.db.get_messages(username=username):
            position = 'right' if message_item.sender.username == self.account_name else 'left'
            item = {
                'position': position,
                'text': f'{message_item.sender.username} {message_item.ru_dt}\n{message_item.message}'
            }
            messages.append(item)
        self.fill_chat_signal.emit(username, messages, clear_field)

    def _users_request(self):
        request = self._action_request(settings.ACTION_GET_USERS)
        self.to_server_messages.append(request)

    def _contacts_request(self):
        request = self._action_request(settings.ACTION_GET_CONTACTS)
        self.to_server_messages.append(request)

    def _clear_status_message(self):
        self.status_message_signal.emit(self.account_name, False)

    def _lost_connection(self):
        self.logger.error(f'Соединение с сервером было потеряно.')
        self.receiving_stop_flag = True
        self.lost_connection_signal.emit()


if __name__ == '__main__':
    client = MsgClient.connect_from_args()
    client.mainloop()
