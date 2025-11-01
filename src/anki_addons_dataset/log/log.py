import logging
from logging import Logger


class Log:

    @staticmethod
    def configure_logging() -> None:
        logging.basicConfig(format='%(asctime)-15s %(levelname)s %(message)s')
        log: Logger = logging.getLogger(__name__.split(".")[0])
        log.setLevel(logging.DEBUG)
