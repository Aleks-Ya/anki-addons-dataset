from datetime import date
from pathlib import Path

from anki_addons_dataset.common.data_types import SnapshotDate
from anki_addons_dataset.common.working_dir import WorkingDir, SnapshotDir


def test_get_path(working_dir_path: Path):
    working_dir: WorkingDir = WorkingDir(working_dir_path)
    assert working_dir.get_path() == working_dir_path


def test_get_history_dir(working_dir_path: Path):
    working_dir: WorkingDir = WorkingDir(working_dir_path)
    assert working_dir.get_history_dir() == working_dir_path / "history"


def test_get_latest_snapshot_dir(working_dir_path: Path):
    working_dir: WorkingDir = WorkingDir(working_dir_path)
    assert working_dir.get_latest_snapshot_dir() is None
    snapshot_date_1: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))
    snapshot_date_2: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-02"))
    snapshot_date_3: SnapshotDate = SnapshotDate(date.fromisoformat("2024-01-01"))
    snapshot_dir_1: SnapshotDir = working_dir.get_snapshot_dir(snapshot_date_1).create()
    snapshot_dir_2: SnapshotDir = working_dir.get_snapshot_dir(snapshot_date_2).create()
    snapshot_dir_3: SnapshotDir = working_dir.get_snapshot_dir(snapshot_date_3).create()
    assert working_dir.list_snapshot_dirs() == [snapshot_dir_3, snapshot_dir_1, snapshot_dir_2]
    assert working_dir.get_latest_snapshot_dir() == snapshot_dir_2


def test_get_snapshot_dir(working_dir_path: Path, snapshot_date: SnapshotDate):
    working_dir: WorkingDir = WorkingDir(working_dir_path)
    snapshot_dir: SnapshotDir = working_dir.get_snapshot_dir(snapshot_date)
    assert snapshot_dir.get_path() == working_dir_path / "history" / "2025-01-25"
    assert not snapshot_dir.get_path().exists()


def test_get_addon_infos_dump(working_dir_path: Path, snapshot_date: SnapshotDate):
    working_dir: WorkingDir = WorkingDir(working_dir_path)
    snapshot_dir: SnapshotDir = working_dir.get_snapshot_dir(snapshot_date)
    assert snapshot_dir.get_addon_infos_dump() == working_dir_path / "history" / "2025-01-25" / "addon-infos.json"


def test_create_final_dir_only_wipes_final(working_dir: WorkingDir, snapshot_date: SnapshotDate):
    snapshot_dir: SnapshotDir = working_dir.get_snapshot_dir(snapshot_date).create()
    stage_marker: Path = snapshot_dir.get_stage_dir() / "marker.txt"
    stage_marker.write_text("keep me")
    dump_file: Path = snapshot_dir.get_addon_infos_dump()
    dump_file.write_text("keep me too")
    stale_final: Path = snapshot_dir.get_final_dir() / "old.json"
    stale_final.write_text("wipe me")

    snapshot_dir.create_final_dir()

    assert stage_marker.exists()
    assert dump_file.exists()
    assert snapshot_dir.get_final_dir().exists()
    assert not stale_final.exists()
