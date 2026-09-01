import logging
from logging import Logger
from pathlib import Path
from typing import Optional

from anki_addons_dataset.argument.script_arguments import Operation
from anki_addons_dataset.bundle.dataset_bundle import DatasetBundle
from anki_addons_dataset.collector.collector_facade import CollectorFacade
from anki_addons_dataset.common.data_types import SnapshotDate, ReportDate, PageLoadTimeout, ElementWaitTimeout
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient
from anki_addons_dataset.info.app_info import AppInfo
from anki_addons_dataset.initializer.working_dir_backup import WorkingDirBackup
from anki_addons_dataset.initializer.working_dir_initializer import WorkingDirInitializer

log: Logger = logging.getLogger(__name__)


class Facade:

    def __init__(self, working_dir: WorkingDir, hugging_face_client: HuggingFaceClient,
                 page_load_timeout: PageLoadTimeout, element_wait_timeout: ElementWaitTimeout):
        self.__working_dir: WorkingDir = working_dir
        self.__hugging_face_client: HuggingFaceClient = hugging_face_client
        self.__page_load_timeout: PageLoadTimeout = page_load_timeout
        self.__element_wait_timeout: ElementWaitTimeout = element_wait_timeout
        self.__collector_facade: CollectorFacade = CollectorFacade(
            working_dir, page_load_timeout, element_wait_timeout)

    def process(self, operation: Operation, snapshot_date: Optional[SnapshotDate], report_date: ReportDate) -> None:
        if operation == Operation.INFO:
            app_info: AppInfo = AppInfo(self.__working_dir, self.__hugging_face_client,
                                        self.__page_load_timeout, self.__element_wait_timeout)
            app_info.print_info(snapshot_date, report_date)
        elif operation == Operation.INIT:
            working_dir_backup: WorkingDirBackup = WorkingDirBackup(self.__working_dir)
            working_dir_initializer: WorkingDirInitializer = WorkingDirInitializer(
                self.__working_dir, self.__hugging_face_client, working_dir_backup)
            working_dir_initializer.initialize_working_dir()
        elif operation == Operation.DOWNLOAD:
            self.__collector_facade.download_snapshot(snapshot_date)
        elif operation == Operation.PARSE:
            self.__collector_facade.parse_snapshots()
        elif operation == Operation.REPORT:
            self.__collector_facade.report_snapshots(report_date)
        elif operation == Operation.BUNDLE:
            dataset_bundle: DatasetBundle = DatasetBundle(self.__working_dir)
            dataset_bundle.create_bundle()
        elif operation == Operation.UPLOAD:
            bundle_dir: Path = self.__working_dir.get_bundle_dir()
            self.__hugging_face_client.tag_backup()
            self.__hugging_face_client.upload_dataset(bundle_dir)
            self.__hugging_face_client.prune_orphans(bundle_dir)
        else:
            raise ValueError(f"Unsupported operation: {operation}")
