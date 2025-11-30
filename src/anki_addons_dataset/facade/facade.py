from datetime import date
import logging
from logging import Logger

from anki_addons_dataset.argument.script_arguments import Operation
from anki_addons_dataset.bundle.dataset_bundle import DatasetBundle
from anki_addons_dataset.collector.collector_facade import CollectorFacade
from anki_addons_dataset.common.working_dir import WorkingDir

log: Logger = logging.getLogger(__name__)


class Facade:

    def __init__(self, working_dir: WorkingDir):
        self.__working_dir: WorkingDir = working_dir
        self.__collector_facade: CollectorFacade = CollectorFacade(working_dir)

    def process(self, operation: Operation, creation_date: date) -> None:
        if operation == Operation.DOWNLOAD:
            self.__download_operation(creation_date)
        elif operation == Operation.PARSE:
            self.__parse_operation()
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    def __download_operation(self, creation_date: date) -> None:
        self.__collector_facade.download_version(creation_date)

    def __parse_operation(self) -> None:
        for version_dir in self.__working_dir.list_version_dirs():
            creation_date: date = version_dir.version_dir_to_creation_date()
            self.__collector_facade.parse_version(creation_date)
        dataset_bundle: DatasetBundle = DatasetBundle(self.__working_dir)
        dataset_bundle.create_bundle()
