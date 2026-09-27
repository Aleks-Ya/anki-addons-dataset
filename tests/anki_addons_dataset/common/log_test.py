import logging
from logging import Logger
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture

from anki_addons_dataset.common.log import Log
from anki_addons_dataset.config.app_config import DEFAULT_LOG_FORMAT, LoggingConfig


def __logging_config(level: int = logging.INFO, log_file: Path = None) -> LoggingConfig:
    return LoggingConfig(level=level, format=DEFAULT_LOG_FORMAT, file=log_file)


def __remove_file_handlers() -> None:
    for handler in list(logging.getLogger().handlers):
        if isinstance(handler, logging.FileHandler):
            logging.getLogger().removeHandler(handler)
            handler.close()


def test_configure_logging(caplog: LogCaptureFixture):
    with caplog.at_level(logging.DEBUG):
        Log.configure_logging()
        logger: Logger = logging.getLogger('anki_addons_dataset')
        logger.debug("A message")
    assert "A message" in caplog.text


def test_cli_level_wins_over_config_level():
    Log.configure_logging()
    Log.apply(__logging_config(level=logging.INFO), cli_level=logging.WARNING)
    assert logging.getLogger('anki_addons_dataset').level == logging.WARNING


def test_config_level_used_when_cli_level_absent():
    Log.configure_logging()
    Log.apply(__logging_config(level=logging.DEBUG), cli_level=None)
    assert logging.getLogger('anki_addons_dataset').level == logging.DEBUG


def test_log_file_is_created_and_written(tmp_path: Path):
    log_file: Path = tmp_path / "nested" / "anki.log"
    Log.configure_logging()
    Log.apply(__logging_config(log_file=log_file), cli_level=None)
    try:
        logging.getLogger('anki_addons_dataset').info("Into the file")
    finally:
        __remove_file_handlers()
    assert "Into the file" in log_file.read_text()


def test_file_gets_debug_while_the_console_keeps_the_requested_level(tmp_path: Path):
    log_file: Path = tmp_path / "anki.log"
    Log.configure_logging()
    Log.apply(__logging_config(level=logging.WARNING, log_file=log_file), cli_level=None)
    try:
        logger: Logger = logging.getLogger('anki_addons_dataset')
        logger.debug("A debug message")
        assert logger.level == logging.DEBUG
        console_levels: list[int] = [handler.level for handler in logging.getLogger().handlers
                                     if not isinstance(handler, logging.FileHandler)]
        assert console_levels
        assert all(level == logging.WARNING for level in console_levels)
    finally:
        __remove_file_handlers()
    assert "A debug message" in log_file.read_text()


def test_parse_level_accepts_any_case():
    assert Log.parse_level("debug") == logging.DEBUG
    assert Log.parse_level("WARNING") == logging.WARNING


def test_parse_level_rejects_unknown_name():
    with pytest.raises(ValueError, match="Not a valid log level: 'NOPE'"):
        Log.parse_level("NOPE")
