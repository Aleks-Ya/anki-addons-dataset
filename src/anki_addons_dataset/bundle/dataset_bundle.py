import shutil
from datetime import date
from pathlib import Path

from anki_addons_dataset.common.working_dir import WorkingDir, VersionDir
from anki_addons_dataset.huggingface.hugging_face import HuggingFace


class DatasetBundle:
    def __init__(self, working_dir: WorkingDir):
        self.__working_dir: WorkingDir = working_dir

    def create_bundle(self, bundle_dir: Path) -> None:
        print(f"Creating dataset bundle in {bundle_dir}")
        shutil.rmtree(bundle_dir, ignore_errors=True)
        bundle_history_dir: Path = bundle_dir / "history"
        bundle_history_dir.mkdir(parents=True, exist_ok=True)
        for version_dir in self.__working_dir.list_version_dirs():
            creation_date: date = version_dir.version_dir_to_creation_date()
            version_bundle_zip: Path = bundle_history_dir / f"{creation_date}.zip"
            print(f"Creating dataset bundle zip: {version_bundle_zip}")
            shutil.make_archive(str(version_bundle_zip), 'zip', version_dir.get_path())

        latest_dir: Path = bundle_dir / "latest"
        print(f"Copying the latest version: {latest_dir}")
        latest_version_dir: VersionDir = self.__working_dir.get_latest_version_dir()
        final_dir: Path = latest_version_dir.get_final_dir()
        shutil.copytree(final_dir, latest_dir)
        metadata_json_file: Path = latest_version_dir.get_metadata_json()
        shutil.copyfile(metadata_json_file, latest_dir / metadata_json_file.name)

        HuggingFace.create_dataset_card(bundle_dir)
