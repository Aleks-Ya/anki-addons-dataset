import logging
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from anki_addons_dataset.config.app_config import LoggingConfig

log: Logger = logging.getLogger(__name__)


class Log:
    __log: Optional[Logger] = None
    __file: Optional[Path] = None

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
        run_file: Optional[Path] = Log.__run_log_file(config.file) if config.file else None
        Log.__file = run_file
        if run_file:
            run_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler: logging.FileHandler = logging.FileHandler(run_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            logging.getLogger().addHandler(file_handler)
        Log.set_log_level(logging.DEBUG if run_file else level)
        if run_file:
            log.info(f"Log file: {run_file}")
            Log.__prune_old_logs(config.file, config.keep)

    @staticmethod
    def active_log_file() -> Optional[Path]:
        return Log.__file

    @staticmethod
    def __run_log_file(file: Path) -> Path:
        return file.with_name(f"{file.stem}-{datetime.now():%Y-%m-%d-%H%M%S}{file.suffix}")

    @staticmethod
    def __prune_old_logs(file: Path, keep: Optional[int]) -> None:
        if keep is None:
            return
        run_files: list[Path] = sorted(file.parent.glob(f"{file.stem}-*{file.suffix}"))
        for outdated in run_files[:-keep]:
            try:
                outdated.unlink()
            except OSError as e:
                log.warning(f"Cannot delete old log file {outdated}: {e}")

    @staticmethod
    def parse_level(name: str) -> int:
        level_name: str = name.upper()
        level_mapping: dict[str, int] = logging.getLevelNamesMapping()
        if level_name not in level_mapping:
            valid_levels: list[str] = list(level_mapping.keys())
            raise ValueError(f"Not a valid log level: '{name}'. Expected one of: {', '.join(valid_levels)}.")
        return level_mapping[level_name]
