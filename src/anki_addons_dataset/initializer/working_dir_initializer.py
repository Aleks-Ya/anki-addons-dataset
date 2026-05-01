import logging
import shutil
from logging import Logger
from pathlib import Path

from anki_addons_dataset.common.data_types import HuggingFaceFolder
from anki_addons_dataset.common.working_dir import WorkingDir, VersionDir
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient
from anki_addons_dataset.initializer.working_dir_backup import WorkingDirBackup

log: Logger = logging.getLogger(__name__)


class WorkingDirInitializer:
    def __init__(self, working_dir: WorkingDir, hugging_face_client: HuggingFaceClient,
                 working_dir_backup: WorkingDirBackup):
        self.__working_dir: WorkingDir = working_dir
        self.__hugging_face_client: HuggingFaceClient = hugging_face_client
        self.__working_dir_backup: WorkingDirBackup = working_dir_backup

    def initialize_working_dir(self) -> None:
        log.info(f"Initializing working directory: {self.__working_dir.get_path()}")
        self.__working_dir_backup.rename_existing_working_dir()
        self.__create_empty_working_dir()
        versions: dict[VersionDir, HuggingFaceFolder] = self.__find_versions_in_hf()
        self.__download_raw_zip_files(versions)

    def __create_empty_working_dir(self):
        self.__working_dir.get_path().mkdir(parents=True, exist_ok=True)
        log.info(f"Created working directory: {self.__working_dir.get_path()}")
        self.__working_dir.get_history_dir().mkdir(parents=True, exist_ok=True)
        log.info(f"Created history directory: {self.__working_dir.get_history_dir()}")

    def __find_versions_in_hf(self) -> dict[VersionDir, HuggingFaceFolder]:
        version_folders: list[HuggingFaceFolder] = self.__hugging_face_client.list_version_folders()
        log.info(f"Found version folders in HF: {version_folders}")
        versions: dict[VersionDir, HuggingFaceFolder] = {self.__hf_folder_to_version_dir(f): f for f in version_folders}
        log.info(f"Target versions in working directory: {versions}")
        return versions

    def __hf_folder_to_version_dir(self, f: HuggingFaceFolder) -> VersionDir:
        version_name: str = f.split('/')[-1]
        return VersionDir(self.__working_dir.get_history_dir() / version_name)

    def __download_raw_zip_files(self, versions: dict[VersionDir, HuggingFaceFolder]):
        log.info(f"Downloading versions")
        for version_dir, hugging_face_folder in versions.items():
            version_dir.create()
            hf_raw_zip: str = f"{hugging_face_folder}/raw.zip"
            cached_raw_zip: Path = self.__hugging_face_client.download_file(hf_raw_zip)
            log.info(f"Downloaded raw.zip from HF: {cached_raw_zip}")
            log.info(f"Unzipping {version_dir.get_path()}")
            shutil.unpack_archive(cached_raw_zip, version_dir.get_raw_dir())
            log.info(f"Unzipped {version_dir.get_path()}")
        log.info(f"Downloaded versions")
