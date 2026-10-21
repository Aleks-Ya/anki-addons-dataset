from pathlib import Path
from typing import Optional

from anki_addons_dataset.common.data_types import Aggregation, AddonInfos, DatasetSnapshotMetadata, RawMetadata, \
    AiTagDefinition, AnkiRelease
from anki_addons_dataset.common.working_dir import SnapshotDir
from anki_addons_dataset.exporter.exporter import Exporter
from anki_addons_dataset.exporter.json.json_exporter import JsonExporter
from anki_addons_dataset.exporter.parquet.parquet_exporter import ParquetExporter
from anki_addons_dataset.exporter.xlsx.xlsx_exporter import XlsxExporter


class ExporterFacade:
    def __init__(self, snapshot_dir: SnapshotDir):
        final_dir: Path = snapshot_dir.get_final_dir()
        self.exporters: list[Exporter] = [
            JsonExporter(final_dir),
            XlsxExporter(final_dir),
            ParquetExporter(final_dir)
        ]

    def export_all(self, addon_infos: AddonInfos, aggregation: Aggregation, tags: list[AiTagDefinition],
                   anki_versions: Optional[list[AnkiRelease]], dataset_snapshot_metadata: DatasetSnapshotMetadata,
                   raw_metadata: RawMetadata) -> None:
        for exporter in self.exporters:
            exporter.export_addon_infos(addon_infos, dataset_snapshot_metadata, raw_metadata)
            exporter.export_aggregation(aggregation, dataset_snapshot_metadata, raw_metadata)
            exporter.export_tags(tags, dataset_snapshot_metadata, raw_metadata)
            if anki_versions is not None:
                exporter.export_anki_versions(anki_versions, dataset_snapshot_metadata, raw_metadata)
