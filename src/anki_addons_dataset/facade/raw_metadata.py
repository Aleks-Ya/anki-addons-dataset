import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from anki_addons_dataset.common.working_dir import VersionDir


class RawMetadata:
    __start_datetime_key: str = "start_timestamp"
    __finis_datetime_key: str = "finish_timestamp"
    __script_version_key: str = "script_version"

    def __init__(self, version_dir: VersionDir) -> None:
        self.__metadata_file: Path = version_dir.get_raw_dir() / "raw-metadata.json"

    def get_start_datetime(self) -> Optional[datetime]:
        return self.__get_datetime_key(self.__start_datetime_key)

    def get_finish_datetime(self) -> Optional[datetime]:
        return self.__get_datetime_key(self.__finis_datetime_key)

    def set_start_datetime(self, start_datetime: datetime) -> None:
        self.__set_datetime_key(self.__start_datetime_key, start_datetime)

    def set_finish_datetime(self, start_datetime: datetime) -> None:
        self.__set_datetime_key(self.__finis_datetime_key, start_datetime)

    def get_script_version(self) -> Optional[str]:
        content: dict[str, Any] = self.__read_content()
        return content.get(self.__script_version_key)

    def set_script_version(self, script_version: str) -> None:
        content: dict[str, Any] = self.__read_content()
        content[self.__script_version_key] = script_version
        self.__write_content(content)

    def __get_datetime_key(self, key: str) -> Optional[datetime]:
        content: dict[str, Any] = self.__read_content()
        value_opt: Optional[str] = content.get(key)
        return datetime.fromisoformat(value_opt) if value_opt else None

    def __set_datetime_key(self, key: str, value: datetime) -> None:
        content: dict[str, Any] = self.__read_content()
        content[key] = value.isoformat()
        self.__write_content(content)

    def __read_content(self) -> dict[str, Any]:
        res_content: dict[str, Any] = {
            self.__start_datetime_key: None,
            self.__finis_datetime_key: None
        }
        if self.__metadata_file.exists():
            content: dict[str, Any] = json.loads(self.__metadata_file.read_text())
            res_content.update(content)
        return res_content

    def __write_content(self, content: dict[str, Any]) -> None:
        self.__metadata_file.parent.mkdir(parents=True, exist_ok=True)
        self.__metadata_file.write_text(json.dumps(content, indent=2))
