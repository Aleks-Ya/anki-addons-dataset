from argparse import ArgumentParser, Namespace, ArgumentTypeError
from datetime import date, datetime
from enum import Enum
from typing import Optional
import logging

from anki_addons_dataset.common.data_types import SnapshotDate, PageLoadTimeout, ElementWaitTimeout


class Operation(Enum):
    INFO = "info"
    INIT = "init"
    DOWNLOAD = "download"
    PARSE = "parse"
    REPORT = "report"
    BUNDLE = "bundle"
    UPLOAD = "upload"


class ScriptArguments:
    def __init__(self):
        parser: ArgumentParser = ArgumentParser()
        parser.add_argument('operations', nargs='+')
        parser.add_argument('-d', '--snapshot-date', type=self.__valid_date)
        parser.add_argument('-l', '--log-level', type=self.__valid_log_level, default='INFO')
        parser.add_argument('--page-load-timeout', type=self.__valid_timeout, default=60)
        parser.add_argument('--element-wait-timeout', type=self.__valid_timeout, default=10)
        self.namespace: Namespace = parser.parse_intermixed_args()

    def get_snapshot_date(self) -> Optional[SnapshotDate]:
        return self.namespace.snapshot_date

    def get_operations(self) -> list[Operation]:
        operations: list[Operation] = []
        for operation in self.namespace.operations:
            if operation.lower() == "all":
                operations.extend(Operation)
            else:
                operations.append(Operation[operation.upper()])
        return operations

    def get_log_level(self) -> int:
        return self.namespace.log_level

    def get_page_load_timeout(self) -> PageLoadTimeout:
        return PageLoadTimeout(self.namespace.page_load_timeout)

    def get_element_wait_timeout(self) -> ElementWaitTimeout:
        return ElementWaitTimeout(self.namespace.element_wait_timeout)

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

    @staticmethod
    def __valid_timeout(s: str) -> int:
        msg: str = f"Not a valid timeout: '{s}'. Expected a positive integer number of seconds."
        try:
            timeout: int = int(s)
        except ValueError:
            raise ArgumentTypeError(msg)
        if timeout <= 0:
            raise ArgumentTypeError(msg)
        return timeout
