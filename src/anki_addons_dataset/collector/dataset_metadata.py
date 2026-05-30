from dataclasses import asdict
from pathlib import Path
from typing import Any
import logging
from logging import Logger

from anki_addons_dataset.common.data_types import DatasetSnapshotMetadata, ReportDate
from anki_addons_dataset.common.json_helper import JsonHelper
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


class DatasetMetadata:

    @staticmethod
    def create_dataset_snapshot_metadata(snapshot_dir: SnapshotDir, script_version: str,
                                         report_date: ReportDate) -> DatasetSnapshotMetadata:
        dataset_snapshot_metadata: DatasetSnapshotMetadata = DatasetSnapshotMetadata(
            data_collection_date=snapshot_dir.snapshot_dir_to_snapshot_date(),
            report_generation_date=report_date,
            script_version=script_version
        )
        log.info(f"Created dataset snapshot metadata: {dataset_snapshot_metadata}")
        return dataset_snapshot_metadata

    @staticmethod
    def write_snapshot_metadata_to_json(snapshot_dir: SnapshotDir,
                                        dataset_snapshot_metadata: DatasetSnapshotMetadata) -> None:
        dest_file: Path = snapshot_dir.get_metadata_json()
        content: dict[str, Any] = asdict(dataset_snapshot_metadata)
        JsonHelper.write_dict_to_file(content, dest_file)
        log.info(f"Created snapshot metadata file: {dest_file}")
