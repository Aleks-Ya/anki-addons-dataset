import dataclasses
import json
import shutil
from pathlib import Path
from typing import Any

from jsonschema import validate

from anki_addons_dataset.common.data_types import AddonInfo, Aggregation
from anki_addons_dataset.exporter.exporter import Exporter
from anki_addons_dataset.exporter.json_addon_info import JsonAddonInfo, Details


class JsonExporter(Exporter):
    def __init__(self, final_dir: Path):
        super().__init__(final_dir / "json")

    def export_addon_infos(self, addon_infos: list[AddonInfo]) -> None:
        json_list: list[Details] = JsonAddonInfo.addon_infos_to_json(addon_infos)
        output_file: Path = self._final_dir / "data.json"
        json_str: str = JsonExporter.__to_json(json_list)
        output_file.write_text(json_str)
        print(f"Write JSON to file: {output_file}")
        schema_file: Path = Path(__file__).parent / "schema.json"
        dataset_schema_file: Path = self._final_dir / "schema.json"
        shutil.copyfile(schema_file, dataset_schema_file)
        self.__verify_schema(output_file, schema_file)

    def export_aggregation(self, aggregation: Aggregation) -> None:
        aggregation_dict: dict[str, int] = dataclasses.asdict(aggregation)
        output_file: Path = self._final_dir / "aggregation.json"
        json_str: str = json.dumps(aggregation_dict, indent=2)
        output_file.write_text(json_str)
        print(f"Write JSON to file: {output_file}")

    @staticmethod
    def __to_json(addons: list[Details]) -> str:
        dicts: list[dict[str, Any]] = [dataclasses.asdict(addon) for addon in addons]
        return json.dumps(dicts, indent=2)

    @staticmethod
    def __verify_schema(doc_file: Path, schema_file: Path) -> None:
        doc_dict: dict[str, Any] = json.loads(doc_file.read_text())
        schema_dict: dict[str, Any] = json.loads(schema_file.read_text())
        validate(instance=doc_dict, schema=schema_dict)
