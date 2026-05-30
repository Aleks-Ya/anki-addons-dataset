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
    operation: Operation = arguments.get_operation()
    assert operation == Operation.DOWNLOAD


def test_parse_operation(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'parse'])
    arguments: ScriptArguments = ScriptArguments()
    snapshot_date: Optional[SnapshotDate] = arguments.get_snapshot_date()
    assert snapshot_date is None
    operation: Operation = arguments.get_operation()
    assert operation == Operation.PARSE


def test_invalid_operation(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'invalid', '-d', '2025-06-10'])
    arguments: ScriptArguments = ScriptArguments()
    with raises(KeyError):
        arguments.get_operation()
