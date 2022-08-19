import logging

# IP адрес по умолчанию для подключения клиента
DEFAULT_IP_ADDRESS = '127.0.0.1'

# Порт по умолчанию
DEFAULT_PORT = 7777

# Максимальная длинна сообщения в байтах
MAX_PACKAGE_LENGTH = 4096

# уровень логирования
LOGGING_LEVEL = logging.INFO
LOGGING_STREAM_COLORED = False
SERVER_LOGGER_NAME = 'server'
CLIENT_LOGGER_NAME = 'client'

# кодировка
ENCODING = 'utf-8'

# Максимальная очередь подключений
MAX_CONNECTIONS = 5

# параметры действий клиента
ACTION_PRESENCE = 'presence'
ACTION_P2P_MESSAGE = 'p2p_message'
ACTION_RESPONSE = 'response'
ACTION_EXIT = 'exit'
ACTION_GET_USERS = 'get_users'
ACTION_GET_CONTACTS = 'get_contacts'
ACTION_ADD_CONTACT = 'add_contact'
ACTION_DEL_CONTACT = 'del_contact'

# параметры запроса
REQUEST_ACTION = 'action'
REQUEST_TIME = 'time'
REQUEST_USER = 'user'
REQUEST_DATA = 'data'
REQUEST_ACCOUNT_NAME = 'account_name'
REQUEST_RECIPIENT = 'recipient'
REQUEST_SENDER = 'sender'
REQUEST_MESSAGE = 'message'
REQUEST_USERS = 'users'
REQUEST_CONTACTS = 'contacts'
REQUEST_USERNAME = 'username'

# параметры ответа
RESPONSE_STATUS = 'status'
RESPONSE_MESSAGE = 'message'
RESPONSE_ERROR = 'error'
