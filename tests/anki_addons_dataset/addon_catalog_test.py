import logging
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any, Optional
from unittest.mock import Mock, patch

import pytest
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from anki_addons_dataset import addon_catalog
from anki_addons_dataset.addon_catalog import _step_snapshot_date, _upload_free, main
from anki_addons_dataset.argument.script_arguments import Operation
from anki_addons_dataset.common.data_types import SnapshotDate
from anki_addons_dataset.config.app_config import AppConfig, SampleConfig


def __arguments(explicit_operation: bool) -> Mock:
    arguments: Mock = Mock()
    arguments.has_explicit_operation.return_value = explicit_operation
    return arguments


def __sampled(app_config: AppConfig) -> AppConfig:
    return replace(app_config, sample=SampleConfig(addons=20))


def test_upload_runs_when_nothing_is_sampled(app_config: AppConfig):
    operations: list[Operation] = list(Operation)
    assert _upload_free(operations, __arguments(False), app_config) == operations


def test_an_explicit_upload_of_a_sampled_run_is_rejected(app_config: AppConfig):
    arguments: Mock = __arguments(True)
    sampled: AppConfig = __sampled(app_config)

    with pytest.raises(ValueError, match="must not be uploaded"):
        _upload_free([Operation.BUNDLE, Operation.UPLOAD], arguments, sampled)


def test_all_drops_upload_from_a_sampled_run(app_config: AppConfig, caplog: LogCaptureFixture):
    operations: list[Operation] = _upload_free(list(Operation), __arguments(False), __sampled(app_config))
    assert Operation.UPLOAD not in operations
    assert Operation.BUNDLE in operations
    assert "Skipping the 'upload' step" in caplog.text


def test_a_sampled_run_without_upload_is_untouched(app_config: AppConfig):
    operations: list[Operation] = [Operation.PARSE, Operation.REPORT]
    assert _upload_free(operations, __arguments(False), __sampled(app_config)) == operations


def test_an_explicit_ai_honours_the_snapshot_date():
    snapshot_date: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))
    assert _step_snapshot_date(__arguments(True), Operation.AI, snapshot_date) == snapshot_date


def test_all_hides_the_snapshot_date_from_ai(caplog: LogCaptureFixture):
    snapshot_date: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))

    assert _step_snapshot_date(__arguments(False), Operation.AI, snapshot_date) is None
    assert "Ignoring -d 2025-01-01 for the 'ai' step" in caplog.text


def test_an_explicit_parse_honours_the_snapshot_date():
    snapshot_date: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))
    assert _step_snapshot_date(__arguments(True), Operation.PARSE, snapshot_date) == snapshot_date


def test_all_hides_the_snapshot_date_from_parse(caplog: LogCaptureFixture):
    snapshot_date: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))

    assert _step_snapshot_date(__arguments(False), Operation.PARSE, snapshot_date) is None
    assert "Ignoring -d 2025-01-01 for the 'parse' step" in caplog.text


def test_an_explicit_report_honours_the_snapshot_date():
    snapshot_date: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))
    assert _step_snapshot_date(__arguments(True), Operation.REPORT, snapshot_date) == snapshot_date


def test_all_hides_the_snapshot_date_from_report(caplog: LogCaptureFixture):
    snapshot_date: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))

    assert _step_snapshot_date(__arguments(False), Operation.REPORT, snapshot_date) is None
    assert "Ignoring -d 2025-01-01 for the 'report' step" in caplog.text


def test_no_snapshot_date_stays_none():
    date_less: Optional[SnapshotDate] = None
    assert _step_snapshot_date(__arguments(True), Operation.AI, date_less) is None


def test_a_failing_run_is_logged_and_exits_with_an_error(monkeypatch: MonkeyPatch, caplog: LogCaptureFixture):
    def failing_run() -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(addon_catalog, "_run", failing_run)

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 1
    assert "Operation failed: boom" in caplog.text
    assert "RuntimeError: boom" in caplog.text


def test_a_system_exit_is_not_swallowed(monkeypatch: MonkeyPatch, caplog: LogCaptureFixture):
    def exiting_run() -> None:
        raise SystemExit(0)

    monkeypatch.setattr(addon_catalog, "_run", exiting_run)

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 0
    assert "Operation failed" not in caplog.text


def test_a_successful_run_returns(monkeypatch: MonkeyPatch):
    monkeypatch.setattr(addon_catalog, "_run", lambda: None)
    main()


def __run(monkeypatch: MonkeyPatch, tmp_path: Path, *cli_args: str) -> Mock:
    monkeypatch.setattr(sys, "argv", ["anki-addons-dataset", *cli_args, "-w", str(tmp_path / "working-dir"),
                                      "-c", str(tmp_path / "missing-config.yaml")])
    with patch.object(addon_catalog, "Facade") as facade_class, \
            patch.object(addon_catalog, "HfApi"), \
            patch.object(addon_catalog.Log, "apply"):
        addon_catalog._run()
    return facade_class.return_value.process


def __steps(process: Mock) -> list[tuple[Operation, Optional[SnapshotDate]]]:
    return [(process_call.args[0], process_call.args[1]) for process_call in process.call_args_list]


def test_run_all_runs_every_step_and_hides_the_date_from_the_offline_steps(
        monkeypatch: MonkeyPatch, tmp_path: Path, caplog: LogCaptureFixture):
    snapshot_date: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))

    with caplog.at_level(logging.INFO):
        process: Mock = __run(monkeypatch, tmp_path, "all", "-d", "2025-01-01")

    assert __steps(process) == [
        (Operation.INFO, snapshot_date), (Operation.INIT, snapshot_date), (Operation.DOWNLOAD, snapshot_date),
        (Operation.SCAN, None), (Operation.AI, None), (Operation.PARSE, None), (Operation.REPORT, None),
        (Operation.BUNDLE, snapshot_date), (Operation.UPLOAD, snapshot_date)]
    report_dates: set[Any] = {process_call.args[2] for process_call in process.call_args_list}
    assert len(report_dates) == 1
    assert "not found, using defaults" in caplog.text
    assert "===== Execution time =====" in caplog.text
    assert "Total" in caplog.text


def test_run_passes_the_date_to_an_explicit_parse(monkeypatch: MonkeyPatch, tmp_path: Path):
    process: Mock = __run(monkeypatch, tmp_path, "parse", "-d", "2025-01-01")

    assert __steps(process) == [(Operation.PARSE, SnapshotDate(date.fromisoformat("2025-01-01")))]


def test_run_all_of_a_sampled_run_skips_upload(monkeypatch: MonkeyPatch, tmp_path: Path):
    process: Mock = __run(monkeypatch, tmp_path, "all", "-d", "2025-01-01", "--sample-addons", "5")

    assert [operation for operation, _ in __steps(process)] == [
        Operation.INFO, Operation.INIT, Operation.DOWNLOAD, Operation.SCAN, Operation.AI, Operation.PARSE,
        Operation.REPORT, Operation.BUNDLE]


def test_run_rejects_an_upload_of_a_sampled_run_before_any_step(monkeypatch: MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(sys, "argv", ["anki-addons-dataset", "bundle", "upload", "--sample-addons", "5",
                                      "-w", str(tmp_path / "working-dir"), "-c", str(tmp_path / "missing.yaml")])
    with patch.object(addon_catalog, "Facade") as facade_class, \
            patch.object(addon_catalog, "HfApi"), \
            patch.object(addon_catalog.Log, "apply"):
        with pytest.raises(ValueError, match="must not be uploaded"):
            addon_catalog._run()

    facade_class.return_value.process.assert_not_called()
