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
            self.__collector_facade.download_version(creation_date)
        elif operation == Operation.PARSE:
            self.__collector_facade.parse_versions()
        elif operation == Operation.BUNDLE:
            dataset_bundle: DatasetBundle = DatasetBundle(self.__working_dir)
            dataset_bundle.create_bundle()
        else:
            raise ValueError(f"Unsupported operation: {operation}")
