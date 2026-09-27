import logging
from logging import Logger
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from anki_addons_dataset.config.app_config import LoggingConfig


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

    @staticmethod
    def apply(config: 'LoggingConfig', cli_level: Optional[int]) -> None:
        level: int = cli_level if cli_level is not None else config.level
        formatter: logging.Formatter = logging.Formatter(config.format)
        for handler in logging.getLogger().handlers:
            handler.setFormatter(formatter)
            handler.setLevel(level)
        if config.file:
            config.file.parent.mkdir(parents=True, exist_ok=True)
            file_handler: logging.FileHandler = logging.FileHandler(config.file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            logging.getLogger().addHandler(file_handler)
        Log.set_log_level(logging.DEBUG if config.file else level)

    @staticmethod
    def parse_level(name: str) -> int:
        level_name: str = name.upper()
        level_mapping: dict[str, int] = logging.getLevelNamesMapping()
        if level_name not in level_mapping:
            valid_levels: list[str] = list(level_mapping.keys())
            raise ValueError(f"Not a valid log level: '{name}'. Expected one of: {', '.join(valid_levels)}.")
        return level_mapping[level_name]
