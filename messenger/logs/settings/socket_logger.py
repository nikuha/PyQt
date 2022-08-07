import sys
import os
import logging
import logging.handlers
sys.path.append(os.path.join(os.getcwd(), '../..'))
from common.settings import LOGGING_LEVEL, LOGGING_STREAM_COLORED, SERVER_LOGGER_NAME, CLIENT_LOGGER_NAME
from logs.settings.colored_formatter import ColoredFormatter


class SocketLogger:
    FILE_FORMATTER = {
        SERVER_LOGGER_NAME: '%(asctime)s %(levelname)s %(filename)s %(message)s (%(filename)s:%(lineno)d)',
        CLIENT_LOGGER_NAME: '%(asctime)s %(levelname)s %(filename)s %(message)s',
    }

    def __init__(self, logger_name):
        if not (logger_name in self.FILE_FORMATTER):
            raise ValueError

        log_path = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(log_path, f'../logfiles/{logger_name}.log')

        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(ColoredFormatter(LOGGING_STREAM_COLORED))
        stream_handler.setLevel(logging.INFO)

        log_file = logging.handlers.TimedRotatingFileHandler(log_path, encoding='utf8',
                                                             interval=1, when='midnight')
        log_file.setFormatter(logging.Formatter(self.FILE_FORMATTER[logger_name]))

        # создаём регистратор и настраиваем его
        self.logger = logging.getLogger(logger_name)
        self.logger.addHandler(stream_handler)
        self.logger.addHandler(log_file)
        self.logger.setLevel(LOGGING_LEVEL)


# отладка
if __name__ == '__main__':
    server_logger = SocketLogger('server')
    server_logger.logger.critical('Серверная Критическая ошибка')
    server_logger.logger.error('Серверная Ошибка')
    server_logger.logger.debug('Серверная Отладочная информация')
    server_logger.logger.info('Серверная Информационное сообщение')

    client_logger = SocketLogger('client')
    client_logger.logger.critical('Клиентская Критическая ошибка')
    client_logger.logger.error('Клиентская Ошибка')
    client_logger.logger.debug('Клиентская Отладочная информация')
    client_logger.logger.info('Клиентская Информационное сообщение')
