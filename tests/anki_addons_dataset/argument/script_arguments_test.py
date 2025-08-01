from datetime import date

import pytest
from _pytest.monkeypatch import MonkeyPatch

from anki_addons_dataset.argument.script_arguments import ScriptArguments, Operation


def test_download_operation(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'download', '-d', '2025-06-10'])
    arguments: ScriptArguments = ScriptArguments()
    creation_date: date = arguments.get_creation_date()
    assert creation_date == date(2025, 6, 10)
    operation: Operation = arguments.get_operation()
    assert operation == Operation.DOWNLOAD


def test_parse_operation(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'parse', '-d', '2025-06-10'])
    arguments: ScriptArguments = ScriptArguments()
    creation_date: date = arguments.get_creation_date()
    assert creation_date == date(2025, 6, 10)
    operation: Operation = arguments.get_operation()
    assert operation == Operation.PARSE


def test_invalid_operation(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'invalid', '-d', '2025-06-10'])
    arguments: ScriptArguments = ScriptArguments()
    with pytest.raises(KeyError):
        arguments.get_operation()
