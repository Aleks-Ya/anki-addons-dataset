import dataclasses
from pathlib import Path
import logging
from logging import Logger

from pandas import DataFrame

from anki_addons_dataset.common.data_types import Aggregation, AddonInfos
from anki_addons_dataset.exporter.exporter import Exporter
from anki_addons_dataset.exporter.json_addon_info import JsonAddonInfo, Details

log: Logger = logging.getLogger(__name__)


class ParquetExporter(Exporter):
    def __init__(self, final_dir: Path):
        super().__init__(final_dir / "parquet")

    def export_addon_infos(self, addon_infos: AddonInfos) -> None:
        json_list: list[Details] = JsonAddonInfo.addon_infos_to_json(addon_infos)
        output_file: Path = self._final_dir / "data.parquet"
        DataFrame(json_list).to_parquet(output_file)
        log.info(f"Write Parquet to file: {output_file}")

    def export_aggregation(self, aggregation: Aggregation) -> None:
        aggregation_dict: dict[str, int] = dataclasses.asdict(aggregation)
        output_file: Path = self._final_dir / "aggregation.parquet"
        DataFrame([aggregation_dict]).to_parquet(output_file)
        log.info(f"Write Parquet to file: {output_file}")
