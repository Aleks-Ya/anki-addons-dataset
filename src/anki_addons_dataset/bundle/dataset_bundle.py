import shutil
from datetime import date
from pathlib import Path

from anki_addons_dataset.common.working_dir import WorkingDir, VersionDir
from anki_addons_dataset.huggingface.hugging_face import HuggingFace


class DatasetBundle:
    def __init__(self, working_dir: WorkingDir):
        self.__working_dir: WorkingDir = working_dir

    def create_bundle(self) -> None:
        bundle_dir: Path = self.__working_dir.get_dataset_dir()
        print(f"Creating dataset bundle in {bundle_dir}")
        shutil.rmtree(bundle_dir, ignore_errors=True)
        bundle_history_dir: Path = bundle_dir / "history"
        bundle_history_dir.mkdir(parents=True, exist_ok=True)
        for version_dir in self.__working_dir.list_version_dirs():
            creation_date: date = version_dir.version_dir_to_creation_date()
            archive_format: str = "zip"
            base_name: str = f"{creation_date}"
            version_bundle_zip: str = str(bundle_history_dir / f"{base_name}")
            print(f"Creating dataset bundle zip: {version_bundle_zip}.{archive_format}")
            shutil.make_archive(version_bundle_zip, archive_format, version_dir.get_path())

        latest_dir: Path = bundle_dir / "latest"
        print(f"Copying the latest version: {latest_dir}")
        latest_version_dir: VersionDir = self.__working_dir.get_latest_version_dir()
        final_dir: Path = latest_version_dir.get_final_dir()
        shutil.copytree(final_dir, latest_dir)
        metadata_json_file: Path = latest_version_dir.get_metadata_json()
        shutil.copyfile(metadata_json_file, latest_dir / metadata_json_file.name)

        HuggingFace.create_dataset_card(bundle_dir)
