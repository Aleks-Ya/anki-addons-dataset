from pathlib import Path
import logging
from logging import Logger

from xlsxwriter import Workbook

from anki_addons_dataset.common.data_types import Aggregation, AddonInfos, DatasetVersionMetadata, RawMetadata
from anki_addons_dataset.exporter.exporter import Exporter
from anki_addons_dataset.exporter.xlsx.addon_info_sheet import AddonInfoSheet
from anki_addons_dataset.exporter.xlsx.aggregation_sheet import AggregationSheet

log: Logger = logging.getLogger(__name__)


class XlsxExporter(Exporter):
    def __init__(self, final_dir: Path):
        super().__init__(final_dir / "xlsx")

    def export_addon_infos(self, addon_infos: AddonInfos, dataset_version_metadata: DatasetVersionMetadata,
                           raw_metadata: RawMetadata):
        output_file: Path = self._final_dir / "data.xlsx"
        workbook: Workbook = Workbook(output_file)
        addon_info_sheet: AddonInfoSheet = AddonInfoSheet(workbook)
        addon_info_sheet.create_sheet(addon_infos, dataset_version_metadata, raw_metadata)
        workbook.close()
        log.info(f"Write XLSX to file: {output_file}")

    def export_aggregation(self, aggregation: Aggregation, dataset_version_metadata: DatasetVersionMetadata,
                           raw_metadata: RawMetadata) -> None:
        output_file: Path = self._final_dir / "aggregation.xlsx"
        workbook: Workbook = Workbook(output_file)
        aggregation_sheet: AggregationSheet = AggregationSheet(workbook)
        aggregation_sheet.create_sheet(aggregation, dataset_version_metadata, raw_metadata)
        workbook.close()
        log.info(f"Write XLSX to file: {output_file}")
