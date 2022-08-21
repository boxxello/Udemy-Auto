import logging
import logging.config
import os

from watcher_udemy.utils import get_app_dir


class CustomFileHandler(logging.FileHandler):
    """
    Allows us to log to the app directory
    """

    def __init__(self, file_name="app.log", mode="a"):
        log_file_path = os.path.join(get_app_dir(), file_name)
        super(CustomFileHandler, self).__init__(log_file_path, mode)


def load_logging_config() -> None:
    """
    Load logging configuration

    :return: None
    """

    my_logger = logging.getLogger("watcher_udemy")
    my_logger.setLevel(logging.INFO)

    # File handler
    file_handler = CustomFileHandler()
    log_format = "%(asctime)s::%(name)s::%(levelname)s::%(module)s: %(message)s"
    formatter = logging.Formatter(fmt=log_format)
    file_handler.setFormatter(formatter)
    my_logger.addHandler(file_handler)

    # Basic format for streamhandler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    my_logger.addHandler(stream_handler)


def get_logger() -> logging.Logger:
    """
    Convenience method to load the app logger

    :return: An instance of the app logger
    """
    return logging.getLogger("watcher_udemy")
