from pathlib import Path
import logging
from logging import Logger

from xlsxwriter import Workbook

from anki_addons_dataset.common.data_types import AddonInfos, DatasetSnapshotMetadata, RawMetadata, \
    AiTagDefinition, AnkiRelease
from anki_addons_dataset.exporter.exporter import Exporter
from anki_addons_dataset.exporter.xlsx.addon_info_sheet import AddonInfoSheet
from anki_addons_dataset.exporter.xlsx.anki_versions_sheet import AnkiVersionsSheet
from anki_addons_dataset.exporter.xlsx.tags_sheet import TagsSheet

log: Logger = logging.getLogger(__name__)


class XlsxExporter(Exporter):
    __font: str = "Carlito"

    def __init__(self, final_dir: Path):
        super().__init__(final_dir / "xlsx")

    def export_addon_infos(self, addon_infos: AddonInfos, dataset_snapshot_metadata: DatasetSnapshotMetadata,
                           raw_metadata: RawMetadata):
        output_file: Path = self._final_dir / "data.xlsx"
        workbook: Workbook = Workbook(output_file, {"default_format_properties": {"font_name": self.__font}})
        addon_info_sheet: AddonInfoSheet = AddonInfoSheet(workbook)
        addon_info_sheet.create_sheet(addon_infos, dataset_snapshot_metadata, raw_metadata)
        workbook.close()
        log.info(f"Write XLSX to file: {output_file}")

    def export_tags(self, tags: list[AiTagDefinition], dataset_snapshot_metadata: DatasetSnapshotMetadata,
                    raw_metadata: RawMetadata) -> None:
        output_file: Path = self._final_dir / "tags.xlsx"
        workbook: Workbook = Workbook(output_file, {"default_format_properties": {"font_name": self.__font}})
        tags_sheet: TagsSheet = TagsSheet(workbook)
        tags_sheet.create_sheet(tags)
        workbook.close()
        log.info(f"Write XLSX to file: {output_file}")

    def export_anki_versions(self, anki_versions: list[AnkiRelease], dataset_snapshot_metadata: DatasetSnapshotMetadata,
                             raw_metadata: RawMetadata) -> None:
        output_file: Path = self._final_dir / "anki_versions.xlsx"
        workbook: Workbook = Workbook(output_file, {"default_format_properties": {"font_name": self.__font}})
        anki_versions_sheet: AnkiVersionsSheet = AnkiVersionsSheet(workbook)
        anki_versions_sheet.create_sheet(anki_versions)
        workbook.close()
        log.info(f"Write XLSX to file: {output_file}")
