from datetime import date
from pathlib import Path
from typing import Optional

from anki_addons_dataset.collector.package.package_cache_index import CachedPackage, PackageCacheIndex, PackageKey
from anki_addons_dataset.common.data_types import AddonId, AnkiPointVersion, SnapshotDate
from anki_addons_dataset.common.working_dir import SnapshotDir, WorkingDir

__ADDON_ID: AddonId = AddonId(100)
__KEY: PackageKey = PackageKey(__ADDON_ID, AnkiPointVersion(45), date(2026, 1, 15))
__FILE_NAME: str = "45-2026-01-15-0123456789ab.ankiaddon"


def __snapshot(working_dir: WorkingDir, day: str) -> SnapshotDir:
    return working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat(day))).create()


def __add_file(snapshot_dir: SnapshotDir, name: str = __FILE_NAME) -> Path:
    file: Path = snapshot_dir.get_package_dir() / str(__ADDON_ID) / name
    file.parent.mkdir(parents=True, exist_ok=True)
    file.touch()
    return file


def test_latest_returns_newest_snapshot_holding_the_key(working_dir: WorkingDir):
    __add_file(__snapshot(working_dir, "2026-02-01"))
    newest_file: Path = __add_file(__snapshot(working_dir, "2026-03-01"))

    index: PackageCacheIndex = PackageCacheIndex.load(working_dir.list_snapshot_dirs())

    cached: Optional[CachedPackage] = index.latest(__KEY)
    assert cached == CachedPackage(newest_file, SnapshotDate(date(2026, 3, 1)))


def test_find_returns_file_by_name(working_dir: WorkingDir):
    file: Path = __add_file(__snapshot(working_dir, "2026-02-01"))

    index: PackageCacheIndex = PackageCacheIndex.load(working_dir.list_snapshot_dirs())

    assert index.find(__ADDON_ID, __FILE_NAME) == file
    assert index.find(AddonId(200), __FILE_NAME) is None


def test_ignores_unexpected_file_names(working_dir: WorkingDir):
    __add_file(__snapshot(working_dir, "2026-02-01"), "45-2026-01-15-part.ankiaddon")

    index: PackageCacheIndex = PackageCacheIndex.load(working_dir.list_snapshot_dirs())

    assert index.size() == 0


def test_snapshot_without_packages_is_empty(working_dir: WorkingDir):
    __snapshot(working_dir, "2026-02-01")

    index: PackageCacheIndex = PackageCacheIndex.load(working_dir.list_snapshot_dirs())

    assert index.latest(__KEY) is None


def test_file_name_starts_with_prefix():
    assert __KEY.file_name("0123456789ab") == __FILE_NAME
    assert __FILE_NAME.startswith(__KEY.file_prefix())
