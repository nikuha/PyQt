import json
import os
import socket
import sys
import select
import argparse
import threading

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox
from configparser import ConfigParser
import common.settings as settings
from common.tcp_socket import TCPSocket
from common.meta import ServerVerifier
from common.descriptors import Port, Address
from server.qt.config_window import ConfigWindow
from server.qt.history_window import HistoryWindow
from server.qt.main_window import MainWindow
from server.qt.users_window import UsersWindow
from logs.settings.socket_logger import SocketLogger
from server.server_db import ServerDB
# from logs.settings.log_decorator import LogDecorator

BASE_DIR = os.getcwd()
CONFIG_FILE = f'{BASE_DIR}/server/server.ini'


class MsgServer(TCPSocket, metaclass=ServerVerifier):
    port = Port()
    address = Address()

    def __init__(self):
        super().__init__()
        socket_logger = SocketLogger(settings.SERVER_LOGGER_NAME)
        self.logger = socket_logger.logger

        self.clients = []
        self.messages = []
        self.names = {}

        self.config = ConfigParser()
        self._load_config()

        self.db = ServerDB(os.path.join(self.config['SETTINGS']['db_path'],
                                        self.config['SETTINGS']['db_file']))

        self.new_connection = False
        self.lock_flag = threading.Lock()
        self.main_window = None

    @classmethod
    def bind_from_args(cls):
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', default=settings.DEFAULT_PORT, type=int, nargs='?')
        parser.add_argument('-a', default=settings.DEFAULT_IP_ADDRESS, nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        address = namespace.a
        port = namespace.p

        sock = cls()
        sock.bind(address, port)
        return sock

    @classmethod
    def bind_from_config(cls):
        sock = cls()
        sock.bind()
        return sock

    # @LogDecorator(settings.SERVER_LOGGER_NAME)
    def bind(self, address=None, port=None):
        if not address:
            address = self.config['SETTINGS']['listen_address']
            if not address:
                address = settings.DEFAULT_IP_ADDRESS
        if not port:
            port = self.config['SETTINGS']['listen_port']
        try:
            self.port = port
        except TypeError as e:
            self.logger.critical(e)
            sys.exit(1)
        self.address = address
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.address, self.port))
        self.sock.settimeout(1)
        self.logger.info(f'Сервер запушен на {address}:{port}')

    def mainloop(self):

        client_listener = threading.Thread(target=self._start_listen)
        client_listener.daemon = True
        client_listener.start()

        self._show_main_window()

    def _show_main_window(self):
        server_app = QApplication(sys.argv)

        self.main_window = MainWindow(self._show_history_window, self._show_config_window, self._show_users_window)
        self.main_window.show_status_message(f'Сервер запущен на {self.address}:{self.port}')
        self._update_connections()

        timer = QTimer()
        timer.timeout.connect(self._update_connections)
        timer.start(1000)

        server_app.exec_()

    def _get_history_data(self):
        return [{
            'username': el.username,
            'sent': f'{el.sent}',
            'received': f'{el.received}',
            'time': f'{el.ru_dt}',
        } for el in self.db.get_users()]

    def _show_history_window(self):
        HistoryWindow(self._get_history_data)

    def _show_users_window(self):
        self.users_window = UsersWindow(self._add_user, self._del_user, self._get_del_users_list)

    def _get_del_users_list(self):
        return sorted([el.username for el in self.db.get_users()])

    def _add_user(self, username, password):
        if self.db.get_user_by_name(username):
            return f'Пользователь {username} уже существует!'
        password_hash = self.get_password_hash(username, password)
        self.db.add_user(username, password_hash)
        return True

    def _del_user(self, username):
        return self.db.del_user(username)

    def _show_config_window(self):
        self.config_window = ConfigWindow(os.path.realpath(
            self.config['SETTINGS']['db_path']),
            self.config['SETTINGS']['db_file'],
            self.config['SETTINGS']['listen_port'],
            self.config['SETTINGS']['listen_address'],
            self._save_config
        )

    def _save_config(self):
        message = QMessageBox()
        self.config['SETTINGS']['db_path'] = self.config_window.db_path.text()
        self.config['SETTINGS']['Database_file'] = self.config_window.db_file.text()
        try:
            port = int(self.config_window.port.text())
            if not 1023 < port < 65535:
                raise ValueError
        except ValueError:
            message.warning(self.config_window, 'Ошибка', 'Порт должен быть числом от 1024 до 65536')
        else:
            self.config['SETTINGS']['listen_address'] = self.config_window.ip.text()
            self.config['SETTINGS']['listen_port'] = self.config_window.port.text()

            with open(CONFIG_FILE, 'w') as conf:
                self.config.write(conf)
                message.information(self.config_window, 'OK', 'Настройки успешно сохранены!')

    def _update_connections(self):
        if self.new_connection:
            connections = [{
                'username': el.user.username,
                'ip': el.ip,
                'port': f'{el.port}',
                'time': f'{el.ru_dt}',
            } for el in self.db.get_connections()]
            self.main_window.fill_table(connections)
            with self.lock_flag:
                self.new_connection = False

    def _start_listen(self):
        self.sock.listen(settings.MAX_CONNECTIONS)
        self.logger.info(f'Слушаем запросы от клиента...')

        try:
            while True:
                try:
                    client_socket, client_address = self.sock.accept()
                except OSError:
                    pass
                else:
                    self.clients.append(client_socket)

                sender_list = []
                recipient_list = []
                try:
                    if self.clients:
                        sender_list, recipient_list, _ = select.select(self.clients, self.clients, [], 0)
                except OSError:
                    pass

                if sender_list:
                    for client_socket in sender_list:
                        try:
                            message = self.get_message(client_socket)
                        except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                            self._close_client_socket(client_socket)
                        except json.JSONDecodeError:
                            self.logger.error(f'Неверный запрос от клиента: {client_socket}')
                            self._close_client_socket(client_socket)
                        else:
                            self._process_message_from_client(client_socket, message)

                while self.messages:
                    message_tuple = self.messages.pop(0)
                    try:
                        self._process_message_to_client(message_tuple, recipient_list)
                    except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                        self._close_client_socket(message_tuple[0])

        except KeyboardInterrupt:
            self._close()

    def _close(self):
        self.sock.close()
        self.logger.info('Завершение работы сервера.')
        sys.exit(0)

    def _get_socket_by_name(self, account_name):
        if account_name not in self.names:
            self.logger.error(f'Пользователь {account_name} не найден!')
            return None
        return self.names[account_name]

    def _get_account_name_by_socket(self, client_socket):
        for name in self.names:
            if self.names[name] == client_socket:
                return name
        return None

    def _close_client_socket(self, client_socket):
        if isinstance(client_socket, str):
            client_socket = self._get_socket_by_name(client_socket)
        if client_socket:
            self.logger.info(f'Клиент {client_socket.getpeername()} отключился от сервера.')
            client_socket.close()
            if account_name := self._get_account_name_by_socket(client_socket):
                self.db.user_logout(account_name)
                with self.lock_flag:
                    self.new_connection = True
            self.names = {key: value for (key, value) in self.names.items() if value != client_socket}
            self.clients.remove(client_socket)

    def _process_message_to_client(self, message_tuple, recipient_list):
        if isinstance(message_tuple[0], str):
            account_name = message_tuple[0]
            client_socket = self._get_socket_by_name(account_name)
        else:
            client_socket = message_tuple[0]
            account_name = None
        if client_socket in recipient_list:
            self.send_message(client_socket, message_tuple[1])
            # if account_name:
            #     if message_tuple[1][settings.REQUEST_ACTION] == settings.ACTION_P2P_MESSAGE:
            #         self.logger.info(f'Сообщение отправлено пользователю {account_name}.')
        else:
            self._close_client_socket(client_socket)

    def _process_message_from_client(self, client_socket, message):
        self.logger.debug(message)
        for param in [settings.REQUEST_ACTION, settings.REQUEST_TIME, settings.REQUEST_USER]:
            if not (param in message):
                self._process_error(client_socket, f'Неверный параметр {param}!')
                return

        if not (account_name := self.get_name_from_message(message)):
            self._process_error(client_socket, f'Неверный параметр {settings.REQUEST_ACCOUNT_NAME}!')
            return
        if account_name not in self.names.keys():
            self.names[account_name] = client_socket

        password = None
        if message[settings.REQUEST_ACTION] in [settings.ACTION_PRESENCE]:
            if not (password := self.get_password_from_message(message)):
                self._process_error(client_socket, f'Неверный параметр {settings.REQUEST_ACCOUNT_NAME}!')
                return

        if message[settings.REQUEST_ACTION] == settings.ACTION_PRESENCE:
            self._process_presence(client_socket, account_name, password)

        elif message[settings.REQUEST_ACTION] == settings.ACTION_EXIT:
            self._close_client_socket(client_socket)

        elif message[settings.REQUEST_ACTION] == settings.ACTION_P2P_MESSAGE:
            self._process_p2p_message(client_socket, message)

        elif message[settings.REQUEST_ACTION] == settings.ACTION_GET_USERS:
            self._process_users(account_name)

        elif message[settings.REQUEST_ACTION] == settings.ACTION_GET_CONTACTS:
            self._process_contacts(account_name)

        elif message[settings.REQUEST_ACTION] == settings.ACTION_ADD_CONTACT:
            self._process_contact(client_socket, account_name, message, 'add')

        elif message[settings.REQUEST_ACTION] == settings.ACTION_DEL_CONTACT:
            self._process_contact(client_socket, account_name, message, 'del')

        else:
            self._process_error(client_socket, f'Неверный параметр {settings.REQUEST_ACTION}!')

    def _process_presence(self, client_socket, account_name, password):
        client_ip, client_port = client_socket.getpeername()
        password_hash = self.get_password_hash(account_name, password)
        login_result = self.db.user_login(account_name, password_hash, client_ip, client_port)
        if login_result is not True:
            self._process_error(client_socket, login_result)
            return
        self.logger.info(f'Пользователь {account_name} онлайн')
        with self.lock_flag:
            self.new_connection = True
        response = self.compose_action_request(settings.ACTION_PRESENCE)
        self.messages.append((account_name, response))

    def _process_p2p_message(self, client_socket, message_from_client):
        if settings.REQUEST_DATA not in message_from_client:
            self._process_error(client_socket, f'Неверный параметр {settings.REQUEST_DATA}!')
            return
        if settings.REQUEST_RECIPIENT not in message_from_client[settings.REQUEST_DATA]:
            self._process_error(client_socket, f'Неверный параметр {settings.REQUEST_RECIPIENT}!')
            return
        if settings.REQUEST_MESSAGE not in message_from_client[settings.REQUEST_DATA]:
            self._process_error(client_socket, f'Неверный параметр {settings.REQUEST_MESSAGE}!')
            return

        recipient = message_from_client[settings.REQUEST_DATA][settings.REQUEST_RECIPIENT]
        sender = self.get_name_from_message(message_from_client)
        msg = message_from_client[settings.REQUEST_DATA][settings.REQUEST_MESSAGE]
        if recipient not in self.names:
            message_to_sender = self.compose_action_request(
                settings.ACTION_P2P_MESSAGE,
                data={settings.REQUEST_STATUS: 400, settings.REQUEST_MESSAGE: 'Польватель не в сети!'}
            )
            self.messages.append((sender, message_to_sender))
            return

        message_to_sender = self.compose_action_request(
            settings.ACTION_P2P_MESSAGE,
            data={
                settings.REQUEST_STATUS: 200,
                settings.REQUEST_RECIPIENT: recipient,
                settings.REQUEST_MESSAGE: msg
            }
        )
        self.messages.append((client_socket, message_to_sender))

        message_to_recipient = self.compose_action_request(settings.ACTION_P2P_MESSAGE, data={
            settings.REQUEST_SENDER: sender,
            settings.REQUEST_MESSAGE: msg
        })
        self.messages.append((recipient, message_to_recipient))

        self.db.process_message(sender, recipient)

    def _process_users(self, account_name):
        users = [user.username for user in self.db.get_users()]
        message_to_client = self.compose_action_request(settings.ACTION_GET_USERS, data={
            settings.REQUEST_USERS: users
        })
        self.messages.append((account_name, message_to_client))

    def _process_contacts(self, account_name):
        contacts = [contact.contact_user.username for contact in self.db.get_contacts_by_username(account_name)]
        message_to_client = self.compose_action_request(settings.ACTION_GET_CONTACTS, data={
            settings.REQUEST_CONTACTS: contacts
        })
        self.messages.append((account_name, message_to_client))

    def _process_contact(self, client_socket, account_name, message_from_client, mode):
        if settings.REQUEST_DATA not in message_from_client:
            self._process_error(client_socket, f'Неверный параметр {settings.REQUEST_DATA}!')
            return
        if settings.REQUEST_USERNAME not in message_from_client[settings.REQUEST_DATA]:
            self._process_error(client_socket, f'Неверный параметр {settings.REQUEST_USERNAME}!')
            return
        contact_user_name = message_from_client[settings.REQUEST_DATA][settings.REQUEST_USERNAME]
        if mode == 'del':
            self.db.del_contact(account_name, contact_user_name)
            action = settings.ACTION_DEL_CONTACT
        else:
            self.db.add_contact(account_name, contact_user_name)
            action = settings.ACTION_ADD_CONTACT
        message_to_client = self.compose_action_request(action, data={
            settings.REQUEST_USERNAME: contact_user_name
        })
        self.messages.append((account_name, message_to_client))

    def _process_error(self, client_socket, message):
        self.messages.append((client_socket, self._compose_response(400, message=message)))

    def _compose_response(self, status, message=None):
        data = {settings.RESPONSE_STATUS: status}
        if message:
            data[settings.RESPONSE_MESSAGE] = message
        return self.compose_action_request(settings.ACTION_RESPONSE, data=data)

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            self.config.read(CONFIG_FILE)
            print('!')
        else:
            self.config['SETTINGS'] = {
                'db_path': '',
                'db_file': 'server.sqlite3',
                'listen_port': settings.DEFAULT_PORT,
                'listen_address': ''
            }
            with open(CONFIG_FILE, 'w') as conf:
                self.config.write(conf)


if __name__ == '__main__':
    server = MsgServer.bind_from_config()
    server.mainloop()
