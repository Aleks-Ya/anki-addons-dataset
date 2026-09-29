from pathlib import Path
from typing import Optional

import pytest
from freezegun import freeze_time

from anki_addons_dataset.common.log import Log
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.initializer.working_dir_backup import WorkingDirBackup


@pytest.fixture(autouse=True)
def no_active_log_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Log, "active_log_file", staticmethod(lambda: None))


def use_log_file(monkeypatch: pytest.MonkeyPatch, log_file: Optional[Path]) -> None:
    monkeypatch.setattr(Log, "active_log_file", staticmethod(lambda: log_file))


def seed_content(working_dir: WorkingDir) -> None:
    (working_dir.get_history_dir() / "2024-01-01").mkdir(parents=True)
    working_dir.get_bundle_dir().mkdir(parents=True)
    (working_dir.get_path() / "logs").mkdir(parents=True)
    (working_dir.get_path() / "notes.txt").write_text("stray")


@freeze_time("2026-05-01 14:25:45")
def test_backup_existing_content(working_dir: WorkingDir, working_dir_backup: WorkingDirBackup,
                                 monkeypatch: pytest.MonkeyPatch):
    seed_content(working_dir)
    log_file: Path = working_dir.get_path() / "logs" / "anki-addons-dataset-2026-05-01-142545.log"
    log_file.write_text("current run")
    use_log_file(monkeypatch, log_file)

    working_dir_backup.backup_existing_content()

    backup_dir: Path = working_dir.get_backups_dir() / "20260501-142545"
    assert working_dir.get_path().exists()
    assert (backup_dir / "history" / "2024-01-01").is_dir()
    assert (backup_dir / "bundle").is_dir()
    assert (backup_dir / "notes.txt").read_text() == "stray"
    assert not working_dir.get_history_dir().exists()
    assert not working_dir.get_bundle_dir().exists()
    assert not (working_dir.get_path() / "notes.txt").exists()
    assert log_file.read_text() == "current run"
    assert not (backup_dir / "logs").exists()


@freeze_time("2026-05-01 14:25:45")
def test_backup_preserves_custom_log_dir(working_dir: WorkingDir, working_dir_backup: WorkingDirBackup,
                                         monkeypatch: pytest.MonkeyPatch):
    seed_content(working_dir)
    log_file: Path = working_dir.get_path() / "my-logs" / "run.log"
    log_file.parent.mkdir(parents=True)
    log_file.write_text("current run")
    use_log_file(monkeypatch, log_file)

    working_dir_backup.backup_existing_content()

    backup_dir: Path = working_dir.get_backups_dir() / "20260501-142545"
    assert log_file.read_text() == "current run"
    assert (backup_dir / "logs").is_dir()
    assert not (backup_dir / "my-logs").exists()


@freeze_time("2026-05-01 14:25:45")
def test_backup_preserves_log_file_in_working_dir_root(working_dir: WorkingDir,
                                                       working_dir_backup: WorkingDirBackup,
                                                       monkeypatch: pytest.MonkeyPatch):
    seed_content(working_dir)
    log_file: Path = working_dir.get_path() / "run.log"
    log_file.write_text("current run")
    use_log_file(monkeypatch, log_file)

    working_dir_backup.backup_existing_content()

    assert log_file.read_text() == "current run"
    assert not (working_dir.get_backups_dir() / "20260501-142545" / "run.log").exists()


@freeze_time("2026-05-01 14:25:45")
def test_backup_moves_logs_when_file_logging_disabled(working_dir: WorkingDir,
                                                      working_dir_backup: WorkingDirBackup):
    seed_content(working_dir)

    working_dir_backup.backup_existing_content()

    backup_dir: Path = working_dir.get_backups_dir() / "20260501-142545"
    assert (backup_dir / "logs").is_dir()
    assert not (working_dir.get_path() / "logs").exists()


@freeze_time("2026-05-01 14:25:45")
def test_backup_ignores_log_file_outside_working_dir(working_dir: WorkingDir,
                                                     working_dir_backup: WorkingDirBackup,
                                                     tmp_path: Path,
                                                     monkeypatch: pytest.MonkeyPatch):
    seed_content(working_dir)
    outside_log_file: Path = tmp_path / "elsewhere" / "run.log"
    outside_log_file.parent.mkdir(parents=True)
    outside_log_file.write_text("current run")
    use_log_file(monkeypatch, outside_log_file)

    working_dir_backup.backup_existing_content()

    assert (working_dir.get_backups_dir() / "20260501-142545" / "logs").is_dir()
    assert outside_log_file.read_text() == "current run"


@freeze_time("2026-05-01 14:25:45")
def test_backup_skips_empty_working_dir(working_dir: WorkingDir, working_dir_backup: WorkingDirBackup):
    working_dir_backup.backup_existing_content()

    assert not working_dir.get_backups_dir().exists()


@freeze_time("2026-05-01 14:25:45")
def test_backup_skips_when_only_preserved_entries(working_dir: WorkingDir,
                                                  working_dir_backup: WorkingDirBackup,
                                                  monkeypatch: pytest.MonkeyPatch):
    log_file: Path = working_dir.get_path() / "logs" / "run.log"
    log_file.parent.mkdir(parents=True)
    log_file.write_text("current run")
    use_log_file(monkeypatch, log_file)
    working_dir.get_backups_dir().mkdir(parents=True)

    working_dir_backup.backup_existing_content()

    assert list(working_dir.get_backups_dir().iterdir()) == []


def test_backup_keeps_earlier_backups(working_dir: WorkingDir, working_dir_backup: WorkingDirBackup):
    with freeze_time("2026-05-01 14:25:45"):
        working_dir.get_history_dir().mkdir(parents=True)
        working_dir_backup.backup_existing_content()
    with freeze_time("2026-05-02 09:00:00"):
        working_dir.get_history_dir().mkdir(parents=True)
        working_dir_backup.backup_existing_content()

    backups: list[str] = sorted(path.name for path in working_dir.get_backups_dir().iterdir())
    assert backups == ["20260501-142545", "20260502-090000"]


def test_backup_skips_missing_working_dir(working_dir: WorkingDir, working_dir_backup: WorkingDirBackup):
    working_dir.get_path().rmdir()

    working_dir_backup.backup_existing_content()

    assert not working_dir.get_path().exists()
