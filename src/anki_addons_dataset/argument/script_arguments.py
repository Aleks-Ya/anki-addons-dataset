from argparse import ArgumentParser, Namespace, ArgumentTypeError
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from anki_addons_dataset.common.data_types import SnapshotDate, PageLoadTimeout, ElementWaitTimeout
from anki_addons_dataset.common.log import Log
from anki_addons_dataset.config.app_config import default_config_file


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
        parser.add_argument('-c', '--config', type=Path, default=None)
        # No default: None means "not passed", so the config file's logging.level can take over.
        parser.add_argument('-l', '--log-level', type=self.__valid_log_level, default=None)
        parser.add_argument('--page-load-timeout', type=self.__valid_timeout, default=120)
        parser.add_argument('--element-wait-timeout', type=self.__valid_timeout, default=120)
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

    def get_config_file(self) -> Path:
        config_file: Optional[Path] = self.namespace.config
        return config_file.expanduser() if config_file else default_config_file()

    def get_log_level(self) -> Optional[int]:
        """The level from `-l`, or None when the flag was not passed (the config file then decides)."""
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
        try:
            return Log.parse_level(s)
        except ValueError as e:
            raise ArgumentTypeError(str(e))

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
