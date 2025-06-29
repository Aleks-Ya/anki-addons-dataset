from datetime import date

from _pytest.monkeypatch import MonkeyPatch

from anki_addons_dataset.argument.script_arguments import ScriptArguments


def test_parse_creation_date(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', '-d', '2025-06-10'])
    arguments: ScriptArguments = ScriptArguments()
    creation_date: date = arguments.get_creation_date()
    assert creation_date == date(2025, 6, 10)
