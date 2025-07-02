from datetime import date
from pathlib import Path

from anki_addons_dataset.common.working_dir import WorkingDir, VersionDir


def test_get_path(working_dir_path: Path):
    working_dir: WorkingDir = WorkingDir(working_dir_path)
    assert working_dir.get_path() == working_dir_path


def test_get_history_dir(working_dir_path: Path):
    working_dir: WorkingDir = WorkingDir(working_dir_path)
    assert working_dir.get_history_dir() == working_dir_path / "history"


def test_get_latest_version_dir(working_dir_path: Path):
    working_dir: WorkingDir = WorkingDir(working_dir_path)
    assert working_dir.get_latest_version_dir() is None
    version_dir_1: VersionDir = working_dir.get_version_dir(date.fromisoformat("2025-01-01")).create()
    version_dir_2: VersionDir = working_dir.get_version_dir(date.fromisoformat("2025-01-02")).create()
    version_dir_3: VersionDir = working_dir.get_version_dir(date.fromisoformat("2024-01-01")).create()
    assert working_dir.list_version_dirs() == [version_dir_3, version_dir_1, version_dir_2]
    assert working_dir.get_latest_version_dir() == version_dir_2


def test_get_version_dir(working_dir_path: Path):
    working_dir: WorkingDir = WorkingDir(working_dir_path)
    version_dir: VersionDir = working_dir.get_version_dir(date.fromisoformat("2025-07-01"))
    assert version_dir.get_path() == working_dir_path / "history" / "2025-07-01"
    assert not version_dir.get_path().exists()
