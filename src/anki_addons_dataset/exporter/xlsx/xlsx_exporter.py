from pathlib import Path

from xlsxwriter import Workbook

from anki_addons_dataset.common.data_types import AddonInfo, Aggregation
from anki_addons_dataset.exporter.exporter import Exporter
from anki_addons_dataset.exporter.xlsx.addon_info_sheet import AddonInfoSheet
from anki_addons_dataset.exporter.xlsx.aggregation_sheet import AggregationSheet


class XlsxExporter(Exporter):

    def export_addon_infos(self, addon_infos: list[AddonInfo]):
        output_file: Path = self._dataset_dir / "anki-addon-catalog.xlsx"
        workbook: Workbook = Workbook(output_file)
        AddonInfoSheet.create_sheet(workbook, addon_infos)
        workbook.close()
        print(f"Write XLSX to file: {output_file}")

    def export_aggregation(self, aggregation: Aggregation) -> None:
        output_file: Path = self._dataset_dir / "aggregation.xlsx"
        workbook: Workbook = Workbook(output_file)
        AggregationSheet.create_sheet(workbook, aggregation)
        workbook.close()
        print(f"Write XLSX to file: {output_file}")
