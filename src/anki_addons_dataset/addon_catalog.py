import logging
import time
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Optional

from huggingface_hub import HfApi

from anki_addons_dataset.argument.script_arguments import ScriptArguments, Operation
from anki_addons_dataset.common.data_types import SnapshotDate, ReportDate, PageLoadTimeout, ElementWaitTimeout
from anki_addons_dataset.common.duration import format_duration
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
    page_load_timeout: PageLoadTimeout = arguments.get_page_load_timeout()
    element_wait_timeout: ElementWaitTimeout = arguments.get_element_wait_timeout()

    hf_api: HfApi = HfApi()
    hugging_face_client: HuggingFaceClient = HuggingFaceClient(hf_api)
    working_dir: WorkingDir = WorkingDir(Path.home() / "anki-addons-dataset")
    facade: Facade = Facade(working_dir, hugging_face_client, page_load_timeout, element_wait_timeout)
    timings: list[tuple[str, float]] = []
    for operation in operations:
        log.info(f"Step '{operation.value}' started")
        start: float = time.perf_counter()
        facade.process(operation, snapshot_date, report_date)
        elapsed: float = time.perf_counter() - start
        timings.append((operation.value, elapsed))
        log.info(f"Step '{operation.value}' completed in {format_duration(elapsed)}")

    total: float = sum(elapsed for _, elapsed in timings)
    log.info("===== Execution time =====")
    for name, elapsed in timings:
        log.info(f"{name:<10} {format_duration(elapsed)}")
    log.info(f"{'Total':<10} {format_duration(total)}")
    log.info("==========================")


if __name__ == "__main__":
    main()
