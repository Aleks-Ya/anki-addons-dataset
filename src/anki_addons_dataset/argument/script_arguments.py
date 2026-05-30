from argparse import ArgumentParser, Namespace, ArgumentTypeError
from datetime import date, datetime
from enum import Enum
from typing import Optional
import logging

from anki_addons_dataset.common.data_types import SnapshotDate


class Operation(Enum):
    INIT = "init"
    DOWNLOAD = "download"
    PARSE = "parse"
    BUNDLE = "bundle"
    UPLOAD = "upload"


class ScriptArguments:
    def __init__(self):
        parser: ArgumentParser = ArgumentParser()
        parser.add_argument('operation')
        parser.add_argument('-d', '--snapshot-date', type=self.__valid_date)
        parser.add_argument('-l', '--log-level', type=self.__valid_log_level, default='INFO')
        self.namespace: Namespace = parser.parse_args()

    def get_snapshot_date(self) -> Optional[SnapshotDate]:
        return self.namespace.snapshot_date

    def get_operation(self) -> Operation:
        return Operation[self.namespace.operation.upper()]

    def get_log_level(self) -> int:
        return self.namespace.log_level

    @staticmethod
    def __valid_date(s: str) -> date:
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            msg: str = f"Not a valid date: '{s}'. Expected format: YYYY-MM-DD."
            raise ArgumentTypeError(msg)

    @staticmethod
    def __valid_log_level(s: str) -> int:
        level_name: str = s.upper()
        level_mapping: dict[str, int] = logging.getLevelNamesMapping()
        if level_name not in level_mapping:
            valid_levels: list[str] = list(level_mapping.keys())
            msg: str = f"Not a valid log level: '{s}'. Expected one of: {', '.join(valid_levels)}."
            raise ArgumentTypeError(msg)
        return level_mapping[level_name]
