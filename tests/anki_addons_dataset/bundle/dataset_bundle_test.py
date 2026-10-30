from datetime import date
from pathlib import Path
import textwrap
from zipfile import ZipFile

from seedir import seedir

from anki_addons_dataset.bundle.dataset_bundle import DatasetBundle
from anki_addons_dataset.collector.package.package_list import PackageList
from anki_addons_dataset.common.data_types import SnapshotDate, ScriptVersion
from anki_addons_dataset.common.working_dir import WorkingDir, SnapshotDir
from anki_addons_dataset.collector.raw_metadata_collector import RawMetadataCollector


def test_parse_snapshot_date(working_dir: WorkingDir, script_version: ScriptVersion):
    snapshot_date_1: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))
    snapshot_dir_1: SnapshotDir = working_dir.get_snapshot_dir(snapshot_date_1).create()
    snapshot_dir_1.get_metadata_json().touch()
    raw_metadata_collector_1: RawMetadataCollector = RawMetadataCollector(snapshot_dir_1)
    raw_metadata_collector_1.set_script_version(script_version)

    snapshot_date_2: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-02"))
    snapshot_dir_2: SnapshotDir = working_dir.get_snapshot_dir(snapshot_date_2).create()
    snapshot_dir_2.get_metadata_json().touch()
    raw_metadata_collector_2: RawMetadataCollector = RawMetadataCollector(snapshot_dir_2)
    raw_metadata_collector_2.set_script_version(script_version)

    assert not working_dir.get_bundle_dir().exists()
    dataset_bundle: DatasetBundle = DatasetBundle(working_dir)
    dataset_bundle.create_bundle()
    tree: str = seedir(working_dir.get_bundle_dir(), printout=False, sort=True)
    assert tree == textwrap.dedent("""\
                                bundle/
                                ├─README.md
                                ├─history/
                                │ ├─2025-01-01/
                                │ │ ├─metadata.json
                                │ │ ├─raw.zip
                                │ │ └─stage.zip
                                │ └─2025-01-02/
                                │   ├─metadata.json
                                │   ├─raw.zip
                                │   └─stage.zip
                                └─latest/
                                  └─metadata.json""")


def __snapshot_with_package(working_dir: WorkingDir, day: str, package_name: str) -> SnapshotDir:
    snapshot_dir: SnapshotDir = working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat(day))).create()
    snapshot_dir.get_metadata_json().touch()
    package_file: Path = snapshot_dir.get_package_dir() / "100" / package_name
    package_file.parent.mkdir(parents=True)
    package_file.write_text("package")
    PackageList.write(snapshot_dir)
    return snapshot_dir


def test_raw_zip_holds_package_list_but_no_packages(working_dir: WorkingDir):
    __snapshot_with_package(working_dir, "2025-01-01", "45-2024-12-01-0123456789ab.ankiaddon")

    DatasetBundle(working_dir).create_bundle()

    raw_zip: Path = working_dir.get_bundle_dir() / "history" / "2025-01-01" / "raw.zip"
    with ZipFile(raw_zip) as archive:
        names: list[str] = archive.namelist()
    assert "package-list.json" in names
    assert not any("5-package" in name or name.endswith(".ankiaddon") for name in names)


def test_raw_zip_keeps_other_raw_files(working_dir: WorkingDir):
    snapshot_dir: SnapshotDir = working_dir.get_snapshot_dir(SnapshotDate(date(2025, 1, 1))).create()
    snapshot_dir.get_metadata_json().touch()
    page: Path = snapshot_dir.get_raw_dir() / "1-anki-web" / "addon" / "100.html"
    page.parent.mkdir(parents=True)
    page.write_text("<html/>")

    DatasetBundle(working_dir).create_bundle()

    with ZipFile(working_dir.get_bundle_dir() / "history" / "2025-01-01" / "raw.zip") as archive:
        assert archive.read("1-anki-web/addon/100.html") == b"<html/>"


def test_bundle_holds_each_package_version_once(working_dir: WorkingDir):
    shared_name: str = "45-2024-12-01-0123456789ab.ankiaddon"
    new_name: str = "45-2025-01-15-ba9876543210.ankiaddon"
    __snapshot_with_package(working_dir, "2025-01-01", shared_name)
    second: SnapshotDir = __snapshot_with_package(working_dir, "2025-02-01", shared_name)
    (second.get_package_dir() / "100" / new_name).write_text("package")

    DatasetBundle(working_dir).create_bundle()

    packages_dir: Path = working_dir.get_bundle_dir() / "packages" / "100"
    assert sorted(file.name for file in packages_dir.iterdir()) == [shared_name, new_name]
