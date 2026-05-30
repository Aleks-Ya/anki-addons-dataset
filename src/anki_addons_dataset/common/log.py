import logging
from logging import Logger
from typing import Optional


class Log:
    __log: Optional[Logger] = None

    @staticmethod
    def configure_logging() -> None:
        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s [%(threadName)-10s] %(message)s')
        logger_name: str = __name__.split(".")[0]
        Log.__log = logging.getLogger(logger_name)
        Log.set_log_level(logging.DEBUG)

    @staticmethod
    def set_log_level(level: int) -> None:
        if Log.__log:
            Log.__log.setLevel(level)
        else:
            raise ValueError("Log not configured")
