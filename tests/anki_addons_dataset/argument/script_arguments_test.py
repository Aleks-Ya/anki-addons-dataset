import logging
from datetime import date
from pathlib import Path
from typing import Optional

import pytest
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


def test_info_operation(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'info'])
    arguments: ScriptArguments = ScriptArguments()
    operations: list[Operation] = arguments.get_operations()
    assert operations == [Operation.INFO]


def test_all_operation(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'all', '-d', '2026-01-01'])
    arguments: ScriptArguments = ScriptArguments()
    snapshot_date: Optional[SnapshotDate] = arguments.get_snapshot_date()
    assert snapshot_date == date(2026, 1, 1)
    operations: list[Operation] = arguments.get_operations()
    assert operations == [Operation.INFO, Operation.INIT, Operation.DOWNLOAD, Operation.AI, Operation.PARSE,
                          Operation.REPORT, Operation.BUNDLE, Operation.UPLOAD]
    assert operations[0] == Operation.INFO


def test_all_operation_expands_in_pipeline_order(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'all'])
    arguments: ScriptArguments = ScriptArguments()
    operations: list[Operation] = arguments.get_operations()
    assert operations == list(Operation)


def test_invalid_operation(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'invalid', '-d', '2025-06-10'])
    arguments: ScriptArguments = ScriptArguments()
    with pytest.raises(KeyError):
        arguments.get_operations()


def test_default_timeouts(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'download', '-d', '2025-06-10'])
    arguments: ScriptArguments = ScriptArguments()
    assert arguments.get_page_load_timeout() == 120
    assert arguments.get_element_wait_timeout() == 120


def test_custom_timeouts(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'download', '-d', '2025-06-10',
                                     '--page-load-timeout', '90', '--element-wait-timeout', '20'])
    arguments: ScriptArguments = ScriptArguments()
    assert arguments.get_page_load_timeout() == 90
    assert arguments.get_element_wait_timeout() == 20


def test_log_level_is_none_when_not_passed(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'parse'])
    # None means "not passed", which lets the config file's logging.level take over.
    assert ScriptArguments().get_log_level() is None


def test_log_level_from_cli(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'parse', '-l', 'warning'])
    assert ScriptArguments().get_log_level() == logging.WARNING


def test_invalid_log_level(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'parse', '-l', 'nope'])
    with pytest.raises(SystemExit):
        ScriptArguments()


def test_default_config_file(monkeypatch: MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'parse'])
    monkeypatch.setenv("HOME", str(tmp_path))
    assert ScriptArguments().get_config_file() == tmp_path / ".anki-addons-dataset.yaml"


def test_custom_config_file(monkeypatch: MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'parse', '--config', '~/custom.yaml'])
    monkeypatch.setenv("HOME", str(tmp_path))  # drives both Path.home() and Path.expanduser()
    assert ScriptArguments().get_config_file() == tmp_path / "custom.yaml"


def test_no_working_dir(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'parse'])
    assert ScriptArguments().get_working_dir() is None


def test_working_dir_from_cli(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'parse', '-w', '/data/anki'])
    assert ScriptArguments().get_working_dir() == Path('/data/anki')


def test_working_dir_is_expanded(monkeypatch: MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'parse', '--working-dir', '~/scratch'])
    monkeypatch.setenv("HOME", str(tmp_path))
    assert ScriptArguments().get_working_dir() == tmp_path / "scratch"


@pytest.mark.parametrize("timeout", ['abc', '0', '-5'])
def test_invalid_timeout(monkeypatch: MonkeyPatch, timeout: str):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'download', '--page-load-timeout', timeout])
    with pytest.raises(SystemExit):
        ScriptArguments()


def test_sample_flags_default_to_none(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'parse'])
    arguments: ScriptArguments = ScriptArguments()
    assert arguments.get_sample_addons() is None
    assert arguments.get_sample_snapshots() is None


def test_sample_flags(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv',
                        ['addon_catalog.py', 'parse', '--sample-addons', '20', '--sample-snapshots', '2'])
    arguments: ScriptArguments = ScriptArguments()
    assert arguments.get_sample_addons() == 20
    assert arguments.get_sample_snapshots() == 2


@pytest.mark.parametrize("value", ['0', '-1', 'x'])
def test_invalid_sample_size(monkeypatch: MonkeyPatch, value: str):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'parse', '--sample-addons', value])
    with pytest.raises(SystemExit):
        ScriptArguments()


def test_has_explicit_operation(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'bundle', 'upload'])
    arguments: ScriptArguments = ScriptArguments()
    assert arguments.has_explicit_operation(Operation.UPLOAD)
    assert not arguments.has_explicit_operation(Operation.PARSE)


def test_has_explicit_operation_is_false_for_all(monkeypatch: MonkeyPatch):
    monkeypatch.setattr('sys.argv', ['addon_catalog.py', 'all', '-d', '2026-01-01'])
    arguments: ScriptArguments = ScriptArguments()
    assert Operation.UPLOAD in arguments.get_operations()
    assert not arguments.has_explicit_operation(Operation.UPLOAD)
