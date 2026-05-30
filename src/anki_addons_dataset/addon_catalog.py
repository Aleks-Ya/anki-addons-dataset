import logging
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Optional

from huggingface_hub import HfApi

from anki_addons_dataset.argument.script_arguments import ScriptArguments, Operation
from anki_addons_dataset.common.data_types import SnapshotDate, ReportDate
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.facade.facade import Facade
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient
from anki_addons_dataset.common.log import Log

log: Logger = logging.getLogger(__name__)

if __name__ == "__main__":
    Log.configure_logging()

    arguments: ScriptArguments = ScriptArguments()

    Log.set_log_level(arguments.get_log_level())
    operation: Operation = arguments.get_operation()
    snapshot_date: Optional[SnapshotDate] = arguments.get_snapshot_date()
    log.info(f"Snapshot date: {snapshot_date}")
    report_date: ReportDate = ReportDate(datetime.now().replace(microsecond=0))
    log.info(f"Report date: {report_date}")

    hf_api: HfApi = HfApi()
    hugging_face_client: HuggingFaceClient = HuggingFaceClient(hf_api)
    working_dir: WorkingDir = WorkingDir(Path.home() / "anki-addons-dataset")
    facade: Facade = Facade(working_dir, hugging_face_client)
    facade.process(operation, snapshot_date, report_date)
