import dataclasses
from pathlib import Path
import logging
from logging import Logger

from pandas import DataFrame

from anki_addons_dataset.common.data_types import Aggregation, AddonInfos, DatasetSnapshotMetadata, RawMetadata, \
    AiTagDefinition, AnkiRelease, ReviewRow
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

    def export_aggregation(self, aggregation: Aggregation, dataset_snapshot_metadata: DatasetSnapshotMetadata,
                           raw_metadata: RawMetadata) -> None:
        aggregation_dict: dict[str, int] = dataclasses.asdict(aggregation)
        output_file: Path = self._final_dir / "aggregation.parquet"
        DataFrame([aggregation_dict]).to_parquet(output_file, compression="zstd")
        log.info(f"Write Parquet to file: {output_file}")

    def export_tags(self, tags: list[AiTagDefinition], dataset_snapshot_metadata: DatasetSnapshotMetadata,
                    raw_metadata: RawMetadata) -> None:
        output_file: Path = self._final_dir / "tags.parquet"
        DataFrame([dataclasses.asdict(tag) for tag in tags]).to_parquet(output_file, compression="zstd")
        log.info(f"Write Parquet to file: {output_file}")

    def export_anki_versions(self, anki_versions: list[AnkiRelease], dataset_snapshot_metadata: DatasetSnapshotMetadata,
                             raw_metadata: RawMetadata) -> None:
        output_file: Path = self._final_dir / "anki_versions.parquet"
        DataFrame([dataclasses.asdict(anki_version) for anki_version in anki_versions],
                  columns=["version", "point_version"]).astype({"version": str, "point_version": "int64"}) \
            .to_parquet(output_file, compression="zstd")
        log.info(f"Write Parquet to file: {output_file}")

    def export_reviews(self, reviews: list[ReviewRow], dataset_snapshot_metadata: DatasetSnapshotMetadata,
                       raw_metadata: RawMetadata) -> None:
        output_file: Path = self._final_dir / "reviews.parquet"
        DataFrame([dataclasses.asdict(review) for review in reviews],
                  columns=["addon_id", "date", "vote", "text", "author_reply"]) \
            .to_parquet(output_file, compression="zstd")
        log.info(f"Write Parquet to file: {output_file}")
