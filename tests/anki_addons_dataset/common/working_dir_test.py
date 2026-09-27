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


def test_get_previous_snapshot_dir(working_dir_path: Path):
    working_dir: WorkingDir = WorkingDir(working_dir_path)
    date_1: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))
    date_2: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-10"))
    date_3: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-20"))
    snapshot_dir_1: SnapshotDir = working_dir.get_snapshot_dir(date_1).create()
    working_dir.get_snapshot_dir(date_3).create()
    assert working_dir.get_previous_snapshot_dir(date_2) == snapshot_dir_1
    assert working_dir.get_previous_snapshot_dir(date_1) is None


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


def test_list_sampled_snapshot_dirs_without_a_limit(working_dir_path: Path):
    working_dir: WorkingDir = WorkingDir(working_dir_path)
    working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat("2025-01-01"))).create()
    working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat("2025-02-01"))).create()
    assert working_dir.list_sampled_snapshot_dirs() == working_dir.list_snapshot_dirs()


def test_list_sampled_snapshot_dirs_keeps_the_newest(working_dir_path: Path):
    working_dir: WorkingDir = WorkingDir(working_dir_path, max_snapshots=2)
    dir_1: SnapshotDir = working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat("2025-01-01"))).create()
    dir_2: SnapshotDir = working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat("2025-02-01"))).create()
    dir_3: SnapshotDir = working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat("2025-03-01"))).create()
    assert working_dir.list_sampled_snapshot_dirs() == [dir_2, dir_3]
    assert working_dir.list_snapshot_dirs() == [dir_1, dir_2, dir_3]


def test_list_sampled_snapshot_dirs_tolerates_a_limit_above_the_history_size(working_dir_path: Path):
    working_dir: WorkingDir = WorkingDir(working_dir_path, max_snapshots=10)
    working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat("2025-01-01"))).create()
    assert len(working_dir.list_sampled_snapshot_dirs()) == 1


def test_sampling_does_not_hide_history_from_the_previous_snapshot_lookup(working_dir_path: Path):
    working_dir: WorkingDir = WorkingDir(working_dir_path, max_snapshots=1)
    date_1: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))
    date_2: SnapshotDate = SnapshotDate(date.fromisoformat("2025-02-01"))
    dir_1: SnapshotDir = working_dir.get_snapshot_dir(date_1).create()
    dir_2: SnapshotDir = working_dir.get_snapshot_dir(date_2).create()
    assert working_dir.list_sampled_snapshot_dirs() == [dir_2]
    assert working_dir.get_previous_snapshot_dir(date_2) == dir_1
    assert working_dir.get_latest_snapshot_dir() == dir_2


def test_get_sample_file(working_dir_path: Path):
    snapshot_dir: SnapshotDir = SnapshotDir(working_dir_path / "history" / "2025-01-01")
    assert snapshot_dir.get_sample_file() == snapshot_dir.get_raw_dir() / "sample.json"
