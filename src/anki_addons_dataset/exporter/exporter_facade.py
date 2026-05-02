from pathlib import Path

from anki_addons_dataset.common.data_types import Aggregation, AddonInfos, DatasetVersionMetadata, RawMetadata
from anki_addons_dataset.common.working_dir import VersionDir
from anki_addons_dataset.exporter.exporter import Exporter
from anki_addons_dataset.exporter.json.json_exporter import JsonExporter
from anki_addons_dataset.exporter.parquet.parquet_exporter import ParquetExporter
from anki_addons_dataset.exporter.xlsx.xlsx_exporter import XlsxExporter


class ExporterFacade:
    def __init__(self, version_dir: VersionDir):
        final_dir: Path = version_dir.get_final_dir()
        self.exporters: list[Exporter] = [
            JsonExporter(final_dir),
            XlsxExporter(final_dir),
            ParquetExporter(final_dir)
        ]

    def export_all(self, addon_infos: AddonInfos, aggregation: Aggregation,
                   dataset_version_metadata: DatasetVersionMetadata, raw_metadata: RawMetadata) -> None:
        for exporter in self.exporters:
            exporter.export_addon_infos(addon_infos, dataset_version_metadata, raw_metadata)
            exporter.export_aggregation(aggregation, dataset_version_metadata, raw_metadata)
