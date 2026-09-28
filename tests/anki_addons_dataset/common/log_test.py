import logging
from logging import Logger
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture
from freezegun import freeze_time

from anki_addons_dataset.common.log import Log
from anki_addons_dataset.config.app_config import DEFAULT_LOG_FORMAT, LoggingConfig


def __logging_config(level: int = logging.INFO, log_file: Path = None,
                     keep: int = None) -> LoggingConfig:
    return LoggingConfig(level=level, format=DEFAULT_LOG_FORMAT, file=log_file, keep=keep)


def __run_logs(directory: Path) -> list[str]:
    return sorted(file.name for file in directory.glob("anki-*.log"))


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
    with freeze_time("2026-09-28 14:30:05"):
        Log.apply(__logging_config(log_file=log_file), cli_level=None)
    try:
        logging.getLogger('anki_addons_dataset').info("Into the file")
    finally:
        __remove_file_handlers()
    run_file: Path = log_file.parent / "anki-2026-09-28-143005.log"
    assert "Into the file" in run_file.read_text()


def test_every_run_gets_its_own_file(tmp_path: Path):
    log_file: Path = tmp_path / "anki.log"
    Log.configure_logging()
    try:
        with freeze_time("2026-09-28 14:30:05"):
            Log.apply(__logging_config(log_file=log_file), cli_level=None)
        logging.getLogger('anki_addons_dataset').info("First run")
        __remove_file_handlers()
        with freeze_time("2026-09-28 18:12:40"):
            Log.apply(__logging_config(log_file=log_file), cli_level=None)
        logging.getLogger('anki_addons_dataset').info("Second run")
    finally:
        __remove_file_handlers()
    assert __run_logs(tmp_path) == ["anki-2026-09-28-143005.log", "anki-2026-09-28-181240.log"]
    assert "Second run" not in (tmp_path / "anki-2026-09-28-143005.log").read_text()
    assert "First run" not in (tmp_path / "anki-2026-09-28-181240.log").read_text()


def test_old_run_logs_beyond_keep_are_deleted(tmp_path: Path):
    log_file: Path = tmp_path / "anki.log"
    for name in ["anki-2026-09-26-100000.log", "anki-2026-09-27-100000.log"]:
        (tmp_path / name).write_text("old")
    Log.configure_logging()
    try:
        with freeze_time("2026-09-28 14:30:05"):
            Log.apply(__logging_config(log_file=log_file, keep=2), cli_level=None)
    finally:
        __remove_file_handlers()
    assert __run_logs(tmp_path) == ["anki-2026-09-27-100000.log", "anki-2026-09-28-143005.log"]


def test_nothing_is_deleted_without_a_keep_limit(tmp_path: Path):
    log_file: Path = tmp_path / "anki.log"
    for name in ["anki-2026-09-26-100000.log", "anki-2026-09-27-100000.log"]:
        (tmp_path / name).write_text("old")
    Log.configure_logging()
    try:
        with freeze_time("2026-09-28 14:30:05"):
            Log.apply(__logging_config(log_file=log_file, keep=None), cli_level=None)
    finally:
        __remove_file_handlers()
    assert len(__run_logs(tmp_path)) == 3


def test_pruning_leaves_unrelated_files_alone(tmp_path: Path):
    log_file: Path = tmp_path / "anki.log"
    (tmp_path / "anki-2026-09-26-100000.log").write_text("old")
    (tmp_path / "anki-2026-09-26-100000.txt").write_text("not a log")
    (tmp_path / "other-2026-09-26-100000.log").write_text("another app")
    Log.configure_logging()
    try:
        with freeze_time("2026-09-28 14:30:05"):
            Log.apply(__logging_config(log_file=log_file, keep=1), cli_level=None)
    finally:
        __remove_file_handlers()
    assert __run_logs(tmp_path) == ["anki-2026-09-28-143005.log"]
    assert (tmp_path / "anki-2026-09-26-100000.txt").is_file()
    assert (tmp_path / "other-2026-09-26-100000.log").is_file()


def test_file_gets_debug_while_the_console_keeps_the_requested_level(tmp_path: Path):
    log_file: Path = tmp_path / "anki.log"
    Log.configure_logging()
    with freeze_time("2026-09-28 14:30:05"):
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
    assert "A debug message" in (tmp_path / "anki-2026-09-28-143005.log").read_text()


def test_parse_level_accepts_any_case():
    assert Log.parse_level("debug") == logging.DEBUG
    assert Log.parse_level("WARNING") == logging.WARNING


def test_parse_level_rejects_unknown_name():
    with pytest.raises(ValueError, match="Not a valid log level: 'NOPE'"):
        Log.parse_level("NOPE")
