import logging

# IP адрес по умолчанию для подключения клиента
DEFAULT_IP_ADDRESS = '127.0.0.1'

# Порт по умолчанию
DEFAULT_PORT = 7776

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

# параметры запроса
REQUEST_ACTION = 'action'
REQUEST_TIME = 'time'
REQUEST_USER = 'user'
REQUEST_DATA = 'data'
REQUEST_ACCOUNT_NAME = 'account_name'
REQUEST_RECIPIENT = 'recipient'
REQUEST_SENDER = 'sender'
REQUEST_MESSAGE = 'message'

# параметры ответа
RESPONSE_STATUS = 'status'
RESPONSE_MESSAGE = 'message'
RESPONSE_ERROR = 'error'
