import binascii
import hashlib
import json
import time
import socket
from .settings import MAX_PACKAGE_LENGTH, ENCODING, REQUEST_ACCOUNT_NAME, REQUEST_PASSWORD
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

    @staticmethod
    def get_password_from_message(message):
        try:
            password_hash = message[REQUEST_USER][REQUEST_PASSWORD]
            return password_hash
        except ValueError:
            return None

    @staticmethod
    def get_password_hash(username, password):
        passwd_bytes = password.encode('utf-8')
        salt = username.lower().encode('utf-8')
        password_hash_b = hashlib.pbkdf2_hmac('sha256', passwd_bytes, salt, 1000)
        password_hash = binascii.hexlify(password_hash_b)
        return password_hash
