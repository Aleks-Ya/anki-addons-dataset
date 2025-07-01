from csv import DictWriter
from pathlib import Path
from typing import Any

from anki_addons_dataset.common.data_types import AddonInfo, Aggregation
from anki_addons_dataset.exporter.exporter import Exporter


class CsvExporter(Exporter):
    def __init__(self, final_dir: Path):
        super().__init__(final_dir / "csv")

    def export_addon_infos(self, addon_infos: list[AddonInfo]):
        output_file: Path = self._final_dir / "data.csv"

        id_field: str = 'ID'
        name_field: str = 'Name'
        rating_field: str = 'Rating'
        stars_field: str = 'Stars'
        fieldnames: list[str] = [id_field, name_field, rating_field, stars_field]

        with open(output_file, 'w') as csv_file:
            writer: DictWriter[str] = DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for addon in addon_infos:
                row: dict[str, Any] = {
                    id_field: addon.header.id,
                    name_field: addon.header.name,
                    rating_field: addon.header.rating,
                    stars_field: addon.github.stars
                }
                writer.writerow(row)
        print(f"Write CSV to file: {output_file}")

    def export_aggregation(self, aggregation: Aggregation) -> None:
        output_file: Path = self._final_dir / "aggregation.csv"

        addon_number_field: str = 'Addon number'
        fieldnames: list[str] = [addon_number_field]

        with open(output_file, 'w') as csv_file:
            writer: DictWriter[str] = DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            row: dict[str, Any] = {
                addon_number_field: aggregation.addon_number
            }
            writer.writerow(row)
        print(f"Write CSV to file: {output_file}")
