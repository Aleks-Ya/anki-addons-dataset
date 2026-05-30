import logging
import shutil
from logging import Logger
from pathlib import Path

from anki_addons_dataset.common.data_types import HuggingFaceFolder
from anki_addons_dataset.common.working_dir import WorkingDir, SnapshotDir
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
        snapshots: dict[SnapshotDir, HuggingFaceFolder] = self.__find_snapshots_in_hf()
        self.__download_raw_zip_files(snapshots)

    def __create_empty_working_dir(self):
        self.__working_dir.get_path().mkdir(parents=True, exist_ok=True)
        log.info(f"Created working directory: {self.__working_dir.get_path()}")
        self.__working_dir.get_history_dir().mkdir(parents=True, exist_ok=True)
        log.info(f"Created history directory: {self.__working_dir.get_history_dir()}")

    def __find_snapshots_in_hf(self) -> dict[SnapshotDir, HuggingFaceFolder]:
        snapshot_folders: list[HuggingFaceFolder] = self.__hugging_face_client.list_snapshot_folders()
        log.info(f"Found snapshot folders in HF: {snapshot_folders}")
        snapshots: dict[SnapshotDir, HuggingFaceFolder] = {self.__hf_folder_to_snapshot_dir(f): f
                                                           for f in snapshot_folders}
        log.info(f"Target snapshots in working directory: {snapshots}")
        return snapshots

    def __hf_folder_to_snapshot_dir(self, f: HuggingFaceFolder) -> SnapshotDir:
        snapshot_name: str = f.split('/')[-1]
        return SnapshotDir(self.__working_dir.get_history_dir() / snapshot_name)

    def __download_raw_zip_files(self, snapshots: dict[SnapshotDir, HuggingFaceFolder]):
        log.info("Downloading snapshots")
        for snapshot_dir, hugging_face_folder in snapshots.items():
            snapshot_dir.create()
            hf_raw_zip: str = f"{hugging_face_folder}/raw.zip"
            cached_raw_zip: Path = self.__hugging_face_client.download_file(hf_raw_zip)
            log.info(f"Downloaded raw.zip from HF: {cached_raw_zip}")
            log.info(f"Unzipping {snapshot_dir.get_path()}")
            shutil.unpack_archive(cached_raw_zip, snapshot_dir.get_raw_dir())
            log.info(f"Unzipped {snapshot_dir.get_path()}")
        log.info("Downloaded snapshots")
