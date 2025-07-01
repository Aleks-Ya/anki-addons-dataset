from pathlib import Path

from anki_addons_dataset.common.data_types import AddonInfo, Aggregation
from anki_addons_dataset.exporter.csv.csv_exporter import CsvExporter
from anki_addons_dataset.exporter.exporter import Exporter
from anki_addons_dataset.exporter.json.json_exporter import JsonExporter
from anki_addons_dataset.exporter.markdown.markdown_exporter import MarkdownExporter
from anki_addons_dataset.exporter.parquet.parquet_exporter import ParquetExporter
from anki_addons_dataset.exporter.xlsx.xlsx_exporter import XlsxExporter


class ExporterFacade:
    def __init__(self, final_dir: Path):
        self.exporters: list[Exporter] = [
            JsonExporter(final_dir),
            MarkdownExporter(final_dir),
            XlsxExporter(final_dir),
            CsvExporter(final_dir),
            ParquetExporter(final_dir)
        ]

    def export_all(self, addon_infos: list[AddonInfo], aggregation: Aggregation) -> None:
        for exporter in self.exporters:
            exporter.export_addon_infos(addon_infos)
            exporter.export_aggregation(aggregation)
