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
from anki_addons_dataset.common.log import Log
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.config.app_config import AppConfig, ConfigLoader
from anki_addons_dataset.facade.facade import Facade
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient

log: Logger = logging.getLogger("anki_addons_dataset.addon_catalog")


def _upload_free(operations: list[Operation], arguments: ScriptArguments, config: AppConfig) -> list[Operation]:
    if not config.sample.is_active() or Operation.UPLOAD not in operations:
        return operations
    if arguments.has_explicit_operation(Operation.UPLOAD):
        raise ValueError("A sampled run must not be uploaded: it would publish a partial dataset. "
                         "Drop 'upload', or drop the sample limits.")
    log.warning("Skipping the 'upload' step: a sampled run must not publish a partial dataset")
    return [operation for operation in operations if operation != Operation.UPLOAD]


def _ai_snapshot_date(arguments: ScriptArguments,
                      snapshot_date: Optional[SnapshotDate]) -> Optional[SnapshotDate]:
    if snapshot_date and not arguments.has_explicit_operation(Operation.AI):
        log.info(f"Ignoring -d {snapshot_date} for the 'ai' step: summarizing every snapshot")
        return None
    return snapshot_date


def main() -> None:
    Log.configure_logging()

    arguments: ScriptArguments = ScriptArguments()

    config_file: Path = arguments.get_config_file()
    config: AppConfig = ConfigLoader.load(config_file) \
        .with_working_dir(arguments.get_working_dir()) \
        .with_sample(arguments.get_sample_addons(), arguments.get_sample_snapshots())
    Log.apply(config.resolved_logging(), arguments.get_log_level())
    log.info(f"Config file: {config_file}" if config_file.is_file()
             else f"Config file: {config_file} (not found, using defaults)")

    operations: list[Operation] = _upload_free(arguments.get_operations(), arguments, config)
    log.info(f"Operations: {[operation.value for operation in operations]}")
    snapshot_date: Optional[SnapshotDate] = arguments.get_snapshot_date()
    ai_snapshot_date: Optional[SnapshotDate] = _ai_snapshot_date(arguments, snapshot_date) \
        if Operation.AI in operations else snapshot_date
    report_date: ReportDate = ReportDate(datetime.now().replace(microsecond=0))
    page_load_timeout: PageLoadTimeout = arguments.get_page_load_timeout()
    element_wait_timeout: ElementWaitTimeout = arguments.get_element_wait_timeout()

    hf_api: HfApi = HfApi()
    hugging_face_client: HuggingFaceClient = HuggingFaceClient(hf_api, config.huggingface)
    working_dir: WorkingDir = WorkingDir(config.working_dir, config.sample.snapshots)
    facade: Facade = Facade(working_dir, hugging_face_client, config, page_load_timeout, element_wait_timeout)
    timings: list[tuple[str, float]] = []
    for operation in operations:
        log.info(f"Step '{operation.value}' started")
        start: float = time.perf_counter()
        facade.process(operation, ai_snapshot_date if operation == Operation.AI else snapshot_date, report_date)
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
