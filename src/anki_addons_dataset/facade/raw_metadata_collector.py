import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from anki_addons_dataset.common.data_types import RawMetadata
from anki_addons_dataset.common.working_dir import VersionDir


class RawMetadataCollector:
    __start_datetime_key: str = "start_timestamp"
    __finish_datetime_key: str = "finish_timestamp"

    def __init__(self, version_dir: VersionDir) -> None:
        self.__metadata_file: Path = version_dir.get_raw_dir() / "raw-metadata.json"

    def set_start_datetime(self, start_datetime: datetime) -> None:
        raw_metadata: RawMetadata = self.read_metadata()
        raw_metadata.start_timestamp = start_datetime
        self.__write_metadata(raw_metadata)

    def set_finish_datetime(self, finish_datetime: datetime) -> None:
        raw_metadata: RawMetadata = self.read_metadata()
        raw_metadata.finish_timestamp = finish_datetime
        self.__write_metadata(raw_metadata)

    def set_script_version(self, script_version: str) -> None:
        raw_metadata: RawMetadata = self.read_metadata()
        raw_metadata.script_version = script_version
        self.__write_metadata(raw_metadata)

    def read_metadata(self) -> RawMetadata:
        if self.__metadata_file.exists():
            content: dict[str, Any] = json.loads(self.__metadata_file.read_text())
            if content.get(self.__start_datetime_key) is not None:
                content[self.__start_datetime_key] = datetime.fromisoformat(content[self.__start_datetime_key])
            if content.get(self.__finish_datetime_key) is not None:
                content[self.__finish_datetime_key] = datetime.fromisoformat(content[self.__finish_datetime_key])
            return RawMetadata(**content)
        else:
            return RawMetadata(None, None, None)

    def __write_metadata(self, raw_metadata: RawMetadata) -> None:
        data = asdict(raw_metadata)
        if data.get(self.__start_datetime_key) is not None:
            data[self.__start_datetime_key] = data[self.__start_datetime_key].isoformat()
        if data.get(self.__finish_datetime_key) is not None:
            data[self.__finish_datetime_key] = data[self.__finish_datetime_key].isoformat()
        self.__metadata_file.write_text(json.dumps(data, indent=2))
