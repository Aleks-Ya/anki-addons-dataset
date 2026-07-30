from datetime import date
from typing import Optional

from pytest import raises
from _pytest.monkeypatch import MonkeyPatch

from anki_addons_dataset.argument.script_arguments import ScriptArguments, Operation
from anki_addons_dataset.common.data_types import SnapshotDate


def test_download_operation(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'download', '-d', '2025-06-10'])
    arguments: ScriptArguments = ScriptArguments()
    snapshot_date: Optional[SnapshotDate] = arguments.get_snapshot_date()
    assert snapshot_date == date(2025, 6, 10)
    operations: list[Operation] = arguments.get_operations()
    assert operations == [Operation.DOWNLOAD]


def test_parse_operation(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'parse'])
    arguments: ScriptArguments = ScriptArguments()
    snapshot_date: Optional[SnapshotDate] = arguments.get_snapshot_date()
    assert snapshot_date is None
    operations: list[Operation] = arguments.get_operations()
    assert operations == [Operation.PARSE]


def test_chained_operations(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'init', 'download', '-d', '2026-01-01', 'parse'])
    arguments: ScriptArguments = ScriptArguments()
    snapshot_date: Optional[SnapshotDate] = arguments.get_snapshot_date()
    assert snapshot_date == date(2026, 1, 1)
    operations: list[Operation] = arguments.get_operations()
    assert operations == [Operation.INIT, Operation.DOWNLOAD, Operation.PARSE]


def test_all_operation(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'all', '-d', '2026-01-01'])
    arguments: ScriptArguments = ScriptArguments()
    snapshot_date: Optional[SnapshotDate] = arguments.get_snapshot_date()
    assert snapshot_date == date(2026, 1, 1)
    operations: list[Operation] = arguments.get_operations()
    assert operations == [Operation.INIT, Operation.DOWNLOAD, Operation.PARSE, Operation.REPORT,
                          Operation.BUNDLE, Operation.UPLOAD]


def test_all_operation_expands_in_pipeline_order(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'all'])
    arguments: ScriptArguments = ScriptArguments()
    operations: list[Operation] = arguments.get_operations()
    assert operations == list(Operation)


def test_invalid_operation(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'invalid', '-d', '2025-06-10'])
    arguments: ScriptArguments = ScriptArguments()
    with raises(KeyError):
        arguments.get_operations()
