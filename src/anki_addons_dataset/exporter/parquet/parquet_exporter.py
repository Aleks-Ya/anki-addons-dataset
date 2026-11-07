import dataclasses
from pathlib import Path
from typing import Any
import logging
from logging import Logger

import pyarrow
from pandas import DataFrame

from anki_addons_dataset.common.data_types import AddonInfos, DatasetSnapshotMetadata, RawMetadata, \
    AiTagDefinition, AnkiRelease, PackageRow, ReviewRow
from anki_addons_dataset.exporter.exporter import Exporter
from anki_addons_dataset.exporter.json_addon_info import JsonAddonInfo, Details

log: Logger = logging.getLogger(__name__)


class ParquetExporter(Exporter):
    def __init__(self, final_dir: Path):
        super().__init__(final_dir / "parquet")

    def export_addon_infos(self, addon_infos: AddonInfos, dataset_snapshot_metadata: DatasetSnapshotMetadata,
                           raw_metadata: RawMetadata) -> None:
        json_list: list[Details] = JsonAddonInfo.addon_infos_to_json(addon_infos)
        output_file: Path = self._final_dir / "data.parquet"
        DataFrame(json_list).to_parquet(output_file, compression="zstd")
        log.info(f"Write Parquet to file: {output_file}")

    def export_tags(self, tags: list[AiTagDefinition], dataset_snapshot_metadata: DatasetSnapshotMetadata,
                    raw_metadata: RawMetadata) -> None:
        output_file: Path = self._final_dir / "tags.parquet"
        DataFrame([dataclasses.asdict(tag) for tag in tags]).to_parquet(output_file, compression="zstd")
        log.info(f"Write Parquet to file: {output_file}")

    def export_anki_versions(self, anki_versions: list[AnkiRelease], dataset_snapshot_metadata: DatasetSnapshotMetadata,
                             raw_metadata: RawMetadata) -> None:
        output_file: Path = self._final_dir / "anki_versions.parquet"
        schema: pyarrow.Schema = pyarrow.schema([("version", pyarrow.string()), ("point_version", pyarrow.int64()),
                                                 ("release_date", pyarrow.date32())])
        DataFrame([dataclasses.asdict(anki_version) for anki_version in anki_versions], columns=schema.names) \
            .to_parquet(output_file, compression="zstd", schema=schema)
        log.info(f"Write Parquet to file: {output_file}")

    def export_reviews(self, reviews: list[ReviewRow]) -> None:
        output_file: Path = self._final_dir / "reviews.parquet"
        DataFrame([dataclasses.asdict(review) for review in reviews],
                  columns=["addon_id", "date", "vote", "text", "author_reply"]) \
            .to_parquet(output_file, compression="zstd")
        log.info(f"Write Parquet to file: {output_file}")

    def export_packages(self, packages: list[PackageRow]) -> None:
        output_file: Path = self._final_dir / "packages.parquet"
        schema: pyarrow.Schema = pyarrow.schema([
            ("addon_id", pyarrow.int64()), ("file_name", pyarrow.string()), ("min_point_version", pyarrow.int64()),
            ("updated", pyarrow.date32()), ("size_bytes", pyarrow.int64()), ("manifest_json", pyarrow.string()),
            ("config_json", pyarrow.string()), ("file_count", pyarrow.int64()),
            ("uncompressed_bytes", pyarrow.int64()), ("python_file_count", pyarrow.int64()),
            ("python_lines", pyarrow.int64()), ("files", pyarrow.list_(pyarrow.string())),
            ("language_bytes",
             pyarrow.list_(pyarrow.struct([("name", pyarrow.string()), ("bytes", pyarrow.int64())])))])
        DataFrame([self.__package_record(package) for package in packages], columns=schema.names) \
            .to_parquet(output_file, compression="zstd", schema=schema)
        log.info(f"Write Parquet to file: {output_file}")

    @staticmethod
    def __package_record(package: PackageRow) -> dict[str, Any]:
        record: dict[str, Any] = dataclasses.asdict(package)
        record["language_bytes"] = [{"name": name, "bytes": count} for name, count in package.language_bytes.items()]
        return record
