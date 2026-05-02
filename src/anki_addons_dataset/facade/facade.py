from datetime import date
import logging
from logging import Logger
from typing import Optional

from anki_addons_dataset.argument.script_arguments import Operation
from anki_addons_dataset.bundle.dataset_bundle import DatasetBundle
from anki_addons_dataset.collector.collector_facade import CollectorFacade
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient
from anki_addons_dataset.initializer.working_dir_backup import WorkingDirBackup
from anki_addons_dataset.initializer.working_dir_initializer import WorkingDirInitializer

log: Logger = logging.getLogger(__name__)


class Facade:

    def __init__(self, working_dir: WorkingDir, hugging_face_client: HuggingFaceClient):
        self.__working_dir: WorkingDir = working_dir
        self.__hugging_face_client: HuggingFaceClient = hugging_face_client
        self.__collector_facade: CollectorFacade = CollectorFacade(working_dir)

    def process(self, operation: Operation, creation_date: Optional[date]) -> None:
        if operation == Operation.INIT:
            working_dir_backup: WorkingDirBackup = WorkingDirBackup(self.__working_dir)
            working_dir_initializer: WorkingDirInitializer = WorkingDirInitializer(
                self.__working_dir, self.__hugging_face_client, working_dir_backup)
            working_dir_initializer.initialize_working_dir()
        elif operation == Operation.DOWNLOAD:
            self.__collector_facade.download_version(creation_date)
        elif operation == Operation.PARSE:
            self.__collector_facade.parse_versions()
        elif operation == Operation.BUNDLE:
            dataset_bundle: DatasetBundle = DatasetBundle(self.__working_dir)
            dataset_bundle.create_bundle()
        elif operation == Operation.UPLOAD:
            self.__hugging_face_client.delete_dataset()
            self.__hugging_face_client.upload_dataset(self.__working_dir.get_bundle_dir())
        else:
            raise ValueError(f"Unsupported operation: {operation}")
