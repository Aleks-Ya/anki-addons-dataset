import logging
from logging import Logger


class Log:

    @staticmethod
    def configure_logging() -> None:
        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s [%(threadName)-10s] %(message)s')
        logger_name: str = __name__.split(".")[0]
        log: Logger = logging.getLogger(logger_name)
        log.setLevel(logging.DEBUG)
