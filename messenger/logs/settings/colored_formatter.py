import logging


class ColoredFormatter(logging.Formatter):
    white = "\x1b[39;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(asctime)s %(levelname)s %(message)s"

    FORMATS = {
        logging.DEBUG: white + format_str + reset,
        logging.INFO: yellow + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def __init__(self, colored=True):
        super().__init__()
        self.colored = colored

    def format(self, record):
        if self.colored:
            log_fmt = self.FORMATS.get(record.levelno)
        else:
            log_fmt = self.format_str
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
