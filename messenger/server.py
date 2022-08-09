import json
import socket
import sys
import select
import argparse
import common.settings as settings
from common.tcp_socket import TCPSocket
from common.meta import ServerVerifier
from common.descriptors import Port
from logs.settings.socket_logger import SocketLogger
# from logs.settings.log_decorator import LogDecorator


class MsgServer(TCPSocket, metaclass=ServerVerifier):
    port = Port()

    def __init__(self):
        super().__init__()
        socket_logger = SocketLogger(settings.SERVER_LOGGER_NAME)
        self.logger = socket_logger.logger
        self.clients = []
        self.messages = []
        self.names = {}

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

    # @LogDecorator(settings.SERVER_LOGGER_NAME)
    def bind(self, address, port):
        try:
            self.port = port
        except TypeError as e:
            self.logger.critical(e)
            sys.exit(1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((address, port))
        self.sock.settimeout(1)
        self.logger.info(f'Сервер запушен на {address}:{port}')

    def start_listen(self):
        self.sock.listen(settings.MAX_CONNECTIONS)
        self.logger.info(f'Слушаем запросы от клиента...')

        try:
            while True:
                try:
                    client_socket, client_address = self.sock.accept()
                except OSError:
                    pass
                else:
                    # self.logger.info(f'Соединение с клиентом: '
                    #                  f'{client_address[0]}:{client_address[1]}')
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
                            self._process_message_from_client(client_socket, message)
                        except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                            self._close_client_socket(client_socket)
                        except json.JSONDecodeError:
                            self.logger.error(f'Неверный запрос от клиента: {client_socket}')
                            self._close_client_socket(client_socket)

                while self.messages:
                    message_tuple = self.messages.pop()
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

    def _close_client_socket(self, client_socket):
        if isinstance(client_socket, str):
            client_socket = self._get_socket_by_name(client_socket)
        if client_socket:
            self.logger.info(f'Клиент {client_socket.getpeername()} отключился от сервера.')
            client_socket.close()
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
            if account_name:
                if message_tuple[1][settings.REQUEST_ACTION] == settings.ACTION_P2P_MESSAGE:
                    self.logger.info(f'Сообщение отправлено пользователю {account_name}.')
        else:
            self._close_client_socket(client_socket)

    def _process_message_from_client(self, client_socket, message):
        self.logger.debug(message)
        for param in [settings.REQUEST_ACTION, settings.REQUEST_TIME, settings.REQUEST_USER]:
            if not (param in message):
                self._process_error(client_socket, f'Неверный параметр {param}!')

        if not (account_name := self.get_name_from_message(message)):
            self._process_error(client_socket, f'Неверный параметр {settings.REQUEST_ACCOUNT_NAME}!')
        if account_name not in self.names.keys():
            self.names[account_name] = client_socket

        if message[settings.REQUEST_ACTION] == settings.ACTION_PRESENCE:
            self._process_presence(account_name)

        elif message[settings.REQUEST_ACTION] == settings.ACTION_EXIT:
            self._close_client_socket(client_socket)

        elif message[settings.REQUEST_ACTION] == settings.ACTION_P2P_MESSAGE:
            self._process_p2p_message(client_socket, message)

        else:
            self._process_error(client_socket, f'Неверный параметр {settings.REQUEST_ACTION}!')

    def _process_presence(self, account_name):
        self.logger.info(f'Пользователь {account_name} онлайн')
        self.messages.append((account_name, self._compose_response(200, message='Вы онлайн.')))

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
            self._process_error(client_socket, f'Пользователь с указанным именем не найден!')
            return

        message_to_client = self.compose_action_request(settings.ACTION_P2P_MESSAGE, data={
            settings.REQUEST_SENDER: sender,
            settings.REQUEST_MESSAGE: msg
        })
        self.messages.append((recipient, message_to_client))

    def _process_error(self, client_socket, message):
        self.messages.append((client_socket, self._compose_response(400, message=message)))

    def _compose_response(self, status, message=None):
        data = {settings.RESPONSE_STATUS: status}
        if message:
            data[settings.RESPONSE_MESSAGE] = message
        return self.compose_action_request(settings.ACTION_RESPONSE, data=data)


if __name__ == '__main__':
    server = MsgServer.bind_from_args()
    server.start_listen()
