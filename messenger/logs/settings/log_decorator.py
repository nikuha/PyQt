import logging
import traceback
import inspect


class LogDecorator:
    def __init__(self, logger_name):
        self.logger = logging.getLogger(logger_name)

    def __call__(self, func_to_log):
        def log_saver(*args, **kwargs):
            func_to_return = func_to_log(*args, **kwargs)
            self.logger.debug(f'Была вызвана функция {func_to_log.__name__} '
                              f'c параметрами {args}, {kwargs}. '
                              f'Вызов из модуля {func_to_log.__module__}. Вызов из'
                              f' функции {traceback.format_stack()[0].strip().split()[-1]}. '
                              f'Вызов из функции {inspect.stack()[1][3]}', stacklevel=2)
            return func_to_return

        return log_saver
