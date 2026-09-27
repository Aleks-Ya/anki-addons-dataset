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
from anki_addons_dataset.config.app_config import AppConfig, ConfigLoader
from anki_addons_dataset.facade.facade import Facade
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient
from anki_addons_dataset.common.log import Log

log: Logger = logging.getLogger("anki_addons_dataset.addon_catalog")


def main() -> None:
    Log.configure_logging()

    arguments: ScriptArguments = ScriptArguments()

    config_file: Path = arguments.get_config_file()
    config: AppConfig = ConfigLoader.load(config_file).with_working_dir(arguments.get_working_dir())
    Log.apply(config.logging, arguments.get_log_level())
    log.info(f"Config file: {config_file}" if config_file.is_file()
             else f"Config file: {config_file} (not found, using defaults)")

    operations: list[Operation] = arguments.get_operations()
    log.info(f"Operations: {[operation.value for operation in operations]}")
    snapshot_date: Optional[SnapshotDate] = arguments.get_snapshot_date()
    report_date: ReportDate = ReportDate(datetime.now().replace(microsecond=0))
    page_load_timeout: PageLoadTimeout = arguments.get_page_load_timeout()
    element_wait_timeout: ElementWaitTimeout = arguments.get_element_wait_timeout()

    hf_api: HfApi = HfApi()
    hugging_face_client: HuggingFaceClient = HuggingFaceClient(hf_api, config.huggingface)
    working_dir: WorkingDir = WorkingDir(config.working_dir)
    facade: Facade = Facade(working_dir, hugging_face_client, config, page_load_timeout, element_wait_timeout)
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
