import dataclasses
import json
from datetime import date
from pathlib import Path
from typing import Any

from anki_addons_dataset.common.data_types import AddonInfo


class JsonHelper:

    @staticmethod
    def write_addon_info_to_file(addon_infos: AddonInfo, file: Path) -> None:
        file.parent.mkdir(parents=True, exist_ok=True)
        content_json: str = json.dumps(dataclasses.asdict(addon_infos), indent=2, default=JsonHelper.__date_serializer)
        file.write_text(content_json)

    @staticmethod
    def write_dict_to_file(content: dict[str, Any], file: Path) -> None:
        file.parent.mkdir(parents=True, exist_ok=True)
        content_json: str = json.dumps(content, indent=2, default=JsonHelper.__date_serializer)
        file.write_text(content_json)

    @staticmethod
    def write_content_to_file(content: str, file: Path) -> None:
        JsonHelper.write_dict_to_file(json.loads(content), file)

    @staticmethod
    def __date_serializer(obj: object):
        if isinstance(obj, date):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
