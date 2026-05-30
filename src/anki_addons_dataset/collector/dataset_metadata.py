from dataclasses import asdict
from pathlib import Path
from typing import Any
import logging
from logging import Logger

from anki_addons_dataset.common.data_types import DatasetVersionMetadata, ReportDate
from anki_addons_dataset.common.json_helper import JsonHelper
from anki_addons_dataset.common.working_dir import VersionDir

log: Logger = logging.getLogger(__name__)


class DatasetMetadata:

    @staticmethod
    def create_dataset_version_metadata(version_dir: VersionDir, script_version: str,
                                        report_date: ReportDate) -> DatasetVersionMetadata:
        dataset_version_metadata: DatasetVersionMetadata = DatasetVersionMetadata(
            data_collection_date=version_dir.version_dir_to_snapshot_date(),
            report_generation_date=report_date,
            script_version=script_version
        )
        log.info(f"Created dataset version metadata: {dataset_version_metadata}")
        return dataset_version_metadata

    @staticmethod
    def write_version_metadata_to_json(version_dir: VersionDir,
                                       dataset_version_metadata: DatasetVersionMetadata) -> None:
        dest_file: Path = version_dir.get_metadata_json()
        content: dict[str, Any] = asdict(dataset_version_metadata)
        JsonHelper.write_dict_to_file(content, dest_file)
        log.info(f"Created dataset metadata file: {dest_file}")
