import os.path
import sys
import json
import argparse
import threading
import time
import common.settings as settings
from common.tcp_socket import TCPSocket
from common.meta import ClientVerifier
from common.descriptors import Port, Address
from db.client_db import ClientDB
from logs.settings.socket_logger import SocketLogger
# from logs.settings.log_decorator import LogDecorator


class MsgClient(TCPSocket, metaclass=ClientVerifier):
    port = Port()
    address = Address()

    def __init__(self):
        super().__init__()

        # self.sock.settimeout(1)

        socket_logger = SocketLogger(settings.CLIENT_LOGGER_NAME)
        self.logger = socket_logger.logger

        self.sock_lock = threading.Lock()
        self.db_lock = threading.Lock()

        self.db = None
        self.user = None

    @classmethod
    def connect_from_args(cls):
        parser = argparse.ArgumentParser()
        parser.add_argument('port', default=settings.DEFAULT_PORT, type=int, nargs='?')
        parser.add_argument('address', default=settings.DEFAULT_IP_ADDRESS, nargs='?')
        parser.add_argument('-n', default='Guest', nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        address = namespace.address
        port = namespace.port
        account_name = namespace.n

        sock = cls()
        sock.connect(address, port, account_name)
        return sock

    # @LogDecorator(settings.CLIENT_LOGGER_NAME)
    def connect(self, address, port, account_name='Guest'):
        try:
            self.port = port
        except TypeError as e:
            self.logger.critical(e)
            sys.exit(1)
        try:
            self.sock.connect((address, port))
            self.user = {settings.REQUEST_ACCOUNT_NAME: account_name}
            self.logger.info(f'Подключились к серверу {address}:{port}, пользователь {account_name}')
            self._send_presence()
            self._init_db()
        except ConnectionRefusedError:
            self.logger.critical(f'Не удалось подключиться к серверу {address}:{port}')
            sys.exit(1)

    @property
    def account_name(self):
        return self.user[settings.REQUEST_ACCOUNT_NAME]

    def mainloop(self):

        receiver = threading.Thread(target=self._getting_server_messages)
        receiver.daemon = True
        receiver.start()

        user_interface = threading.Thread(target=self._interactive)
        user_interface.daemon = True
        user_interface.start()

        try:
            while True:
                time.sleep(1)
                if receiver.is_alive() and user_interface.is_alive():
                    continue
                break
        except (KeyboardInterrupt, SystemExit):
            receiver.join()
            self._close()

    def _init_db(self):
        filename = f'client_{self.account_name}.sqlite3'
        self.db = ClientDB(os.path.join(os.getcwd(), 'db', filename))
        self._users_request()
        time.sleep(1)
        self._contacts_request()

    def _send_presence(self):
        self.send_message(self.sock, self._action_request(settings.ACTION_PRESENCE))
        self.logger.info(self._get_message_response())

    def _close(self, reason='client'):
        self.sock.close()
        if reason == 'client':
            self.logger.info('Завершение работы по команде пользователя.')
        else:
            self.logger.info('Завершение работы по причине: ' + reason)
        sys.exit(0)

    def _lost_connection(self):
        self.logger.error(f'Соединение с сервером было потеряно.')
        sys.exit(1)

    def _get_message_response(self):
        # with self.sock_lock:
        try:
            message = self.get_message(self.sock)
            # self.logger.info(message)
            if settings.REQUEST_ACTION not in message:
                raise ValueError(settings.REQUEST_ACTION)

            if message[settings.REQUEST_ACTION] == settings.ACTION_RESPONSE:
                if settings.REQUEST_DATA not in message:
                    raise ValueError(settings.REQUEST_DATA)
                return self._get_response(message[settings.REQUEST_DATA])

            if message[settings.REQUEST_ACTION] == settings.ACTION_P2P_MESSAGE:
                if settings.REQUEST_DATA not in message:
                    raise ValueError(settings.REQUEST_DATA)
                return self._get_p2p_message(message[settings.REQUEST_DATA])

            if message[settings.REQUEST_ACTION] == settings.ACTION_GET_USERS:
                if settings.REQUEST_DATA not in message:
                    raise ValueError(settings.REQUEST_DATA)
                return self._get_users(message[settings.REQUEST_DATA])

            if message[settings.REQUEST_ACTION] == settings.ACTION_GET_CONTACTS:
                if settings.REQUEST_DATA not in message:
                    raise ValueError(settings.REQUEST_DATA)
                return self._get_contacts(message[settings.REQUEST_DATA])

            raise ValueError
        except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError):
            self._lost_connection()
        except json.JSONDecodeError:
            return None
        except ValueError as e:
            return 'Неверный ответ сервера!' + e

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

    @staticmethod
    def _get_p2p_message(data):
        try:
            if not (settings.RESPONSE_MESSAGE in data and settings.REQUEST_SENDER in data):
                raise ValueError
            print(f'\nСообщение от {data[settings.REQUEST_SENDER]}: \n' +
                  f'{data[settings.RESPONSE_MESSAGE]}')
            return None
        except (ValueError, json.JSONDecodeError):
            return 'Неизвестный статус ответа сервера!'

    def _get_users(self, data):
        try:
            if not (settings.REQUEST_USERS in data):
                raise ValueError
            self.db.add_users(data[settings.REQUEST_USERS])
            return None
        except (ValueError, json.JSONDecodeError):
            return 'Неизвестный статус ответа сервера!'

    def _get_contacts(self, data):
        try:
            if not (settings.REQUEST_CONTACTS in data):
                raise ValueError
            for contact in data[settings.REQUEST_CONTACTS]:
                self.db.add_contact(contact)
            return None
        except (ValueError, json.JSONDecodeError):
            return 'Неизвестный статус ответа сервера!'


    @staticmethod
    def _print_help():
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    def _create_message(self):
        recipient = input('Введите получателя сообщения: ')
        input_message = input('Введите сообщение для отправки: ')
        message = self._action_request(settings.ACTION_P2P_MESSAGE, data={
            settings.REQUEST_RECIPIENT: recipient,
            settings.REQUEST_MESSAGE: input_message
        })
        with self.db_lock:
            self.db.save_message(self.account_name, recipient, input_message)
        # with self.sock_lock:
        try:
            self.send_message(self.sock, message)
        except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
            self._lost_connection()

    def _exit_message(self):
        # with self.sock_lock:
        try:
            self.send_message(self.sock, self._action_request(settings.ACTION_EXIT))
        except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
            self._lost_connection()

    def _users_request(self):
        # with self.sock_lock:
        try:
            self.send_message(self.sock, self._action_request(settings.ACTION_GET_USERS))
        except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
            self._lost_connection()

    def _contacts_request(self):
        # with self.sock_lock:
        try:
            request = self._action_request(settings.ACTION_GET_CONTACTS)
            self.send_message(self.sock, request)
        except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
            self._lost_connection()

    def _getting_server_messages(self):
        while True:
            time.sleep(1)
            # with self.sock_lock:
            if response := self._get_message_response():
                self.logger.info(response)

    def _interactive(self):
        self._print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self._create_message()
            elif command == 'help':
                self._print_help()
            elif command == 'exit':
                self._exit_message()
                time.sleep(0.5)
                break
            else:
                print('Неизвестная команда. Воспользуйтесь help')


if __name__ == '__main__':
    client = MsgClient.connect_from_args()
    client.mainloop()
