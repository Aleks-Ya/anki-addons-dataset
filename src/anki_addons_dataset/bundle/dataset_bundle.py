import logging
import shutil
from datetime import date
from logging import Logger
from pathlib import Path

from anki_addons_dataset.common.working_dir import WorkingDir, VersionDir
from anki_addons_dataset.huggingface.hugging_face import HuggingFace

log: Logger = logging.getLogger(__name__)


class DatasetBundle:
    def __init__(self, working_dir: WorkingDir):
        self.__working_dir: WorkingDir = working_dir

    def create_bundle(self) -> None:
        bundle_dir: Path = self.__working_dir.get_dataset_dir()
        log.info(f"Creating dataset bundle in {bundle_dir}")
        shutil.rmtree(bundle_dir, ignore_errors=True)
        bundle_history_dir: Path = bundle_dir / "history"
        bundle_history_dir.mkdir(parents=True, exist_ok=True)
        for version_dir in self.__working_dir.list_version_dirs():
            raw_dir: Path = version_dir.get_raw_dir()
            creation_date: date = version_dir.version_dir_to_creation_date()
            base_name: str = f"{creation_date}"
            output_dir: Path = bundle_history_dir / base_name
            self.__create_zip(raw_dir, output_dir, "raw")

        latest_dir: Path = bundle_dir / "latest"
        log.info(f"Copying the latest version: {latest_dir}")
        latest_version_dir: VersionDir = self.__working_dir.get_latest_version_dir()
        final_dir: Path = latest_version_dir.get_final_dir()
        shutil.copytree(final_dir, latest_dir)
        metadata_json_file: Path = latest_version_dir.get_metadata_json()
        shutil.copyfile(metadata_json_file, latest_dir / metadata_json_file.name)

        HuggingFace.create_dataset_card(bundle_dir)

    @staticmethod
    def __create_zip(source_dir: Path, output_dir: Path, output_base_name: str) -> None:
        zip_base_name: str = str(output_dir / f"{output_base_name}")
        archive_format: str = "zip"
        log.info(f"Creating zip: {zip_base_name}.{archive_format}")
        shutil.make_archive(zip_base_name, archive_format, source_dir)
