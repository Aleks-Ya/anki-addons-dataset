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

log: Logger = logging.getLogger("anki_addons_dataset.addon_catalog")


def main() -> None:
    Log.configure_logging()

    arguments: ScriptArguments = ScriptArguments()

    Log.set_log_level(arguments.get_log_level())
    operations: list[Operation] = arguments.get_operations()
    log.info(f"Operations: {[operation.value for operation in operations]}")
    snapshot_date: Optional[SnapshotDate] = arguments.get_snapshot_date()
    report_date: ReportDate = ReportDate(datetime.now().replace(microsecond=0))

    hf_api: HfApi = HfApi()
    hugging_face_client: HuggingFaceClient = HuggingFaceClient(hf_api)
    working_dir: WorkingDir = WorkingDir(Path.home() / "anki-addons-dataset")
    facade: Facade = Facade(working_dir, hugging_face_client)
    for operation in operations:
        facade.process(operation, snapshot_date, report_date)


if __name__ == "__main__":
    main()
