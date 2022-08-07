import json
import time
import socket
from .settings import MAX_PACKAGE_LENGTH, ENCODING, RESPONSE_STATUS, REQUEST_ACCOUNT_NAME
from .settings import REQUEST_ACTION, REQUEST_TIME, REQUEST_USER, REQUEST_DATA


class TCPSocket:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @staticmethod
    def get_message(sock: socket):
        encoded_response = sock.recv(MAX_PACKAGE_LENGTH)
        if isinstance(encoded_response, bytes):
            json_response = encoded_response.decode(ENCODING)
            response = json.loads(json_response)
            if isinstance(response, dict):
                return response
            raise ValueError
        raise ValueError

    @staticmethod
    def send_message(sock: socket, message: dict):
        if not isinstance(message, dict):
            raise ValueError
        js_message = json.dumps(message)
        sock.send(js_message.encode(ENCODING))
        return True

    @staticmethod
    def int_port(port):
        try:
            port = int(port)
            if not 1023 < port < 65535:
                raise ValueError
        except ValueError:
            return None
        return port

    def compose_action_request(self, action, user=None, data=None):
        request = {
            REQUEST_ACTION: action,
            REQUEST_TIME: time.time()
        }
        if user:
            request[REQUEST_USER] = user
        elif hasattr(self, 'user'):
            request[REQUEST_USER] = self.user
        if data:
            request[REQUEST_DATA] = data
        return request

    @staticmethod
    def get_name_from_message(message):
        try:
            name = message[REQUEST_USER][REQUEST_ACCOUNT_NAME]
            return name
        except ValueError:
            return None
