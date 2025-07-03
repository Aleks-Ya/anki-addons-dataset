from datetime import date
from pathlib import Path

from anki_addons_dataset.bundle.dataset_bundle import DatasetBundle
from anki_addons_dataset.common.working_dir import WorkingDir, VersionDir
from anki_addons_dataset.facade.raw_metadata import RawMetadata


def test_parse_creation_date(working_dir: WorkingDir):
    version_dir_1: VersionDir = working_dir.get_version_dir(date.fromisoformat("2025-01-01")).create()
    version_dir_1.get_final_dir().mkdir(parents=True, exist_ok=True)
    version_dir_1.get_metadata_json().touch()
    raw_metadata_1: RawMetadata = RawMetadata(version_dir_1)
    raw_metadata_1.set_script_version("v0.0.1")

    version_dir_2: VersionDir = working_dir.get_version_dir(date.fromisoformat("2025-01-02")).create()
    version_dir_2.get_final_dir().mkdir(parents=True, exist_ok=True)
    version_dir_2.get_metadata_json().touch()
    raw_metadata_2: RawMetadata = RawMetadata(version_dir_2)
    raw_metadata_2.set_script_version("v0.0.1")

    bundle_history_dir: Path = working_dir.get_path() / "dataset" / "history"
    assert not bundle_history_dir.exists()
    dataset_bundle: DatasetBundle = DatasetBundle(working_dir)
    dataset_bundle.create_bundle()
    act_version_zips: list[str] = sorted([version_zip.name for version_zip in bundle_history_dir.iterdir()])
    assert act_version_zips == ['2025-01-01.zip', '2025-01-02.zip']
