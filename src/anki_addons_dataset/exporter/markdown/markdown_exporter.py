from pathlib import Path
import logging
from logging import Logger

from mdutils import MdUtils

from anki_addons_dataset.common.data_types import AddonInfo, Aggregation
from anki_addons_dataset.exporter.exporter import Exporter

log: Logger = logging.getLogger(__name__)


class MarkdownExporter(Exporter):
    def __init__(self, final_dir: Path):
        super().__init__(final_dir / "markdown")

    def export_addon_infos(self, addon_infos: list[AddonInfo]):
        output_file: Path = self._final_dir / "data.md"
        md: MdUtils = MdUtils(file_name=str(output_file), title='Anki Addons Catalog for Programmers')
        md.new_line()
        lines: list[str] = ["ID", "Name", "Rating", "Stars"]
        column_number: int = len(lines)
        for addon in addon_infos:
            line: list[str] = [addon.header.id, addon.header.name, addon.header.rating, addon.github.stars]
            lines.extend(line)
        md.new_table(column_number, len(addon_infos) + 1, lines)
        md.create_md_file()
        log.info(f"Write MarkDown to file: {output_file}")

    def export_aggregation(self, aggregation: Aggregation) -> None:
        output_file: Path = self._final_dir / "aggregation.md"
        md: MdUtils = MdUtils(file_name=str(output_file), title='Anki Addons Catalog for Programmers')
        md.new_line(f"Addon number: {aggregation.addon_number}")
        md.create_md_file()
        log.info(f"Write MarkDown to file: {output_file}")
