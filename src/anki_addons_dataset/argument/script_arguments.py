from argparse import ArgumentParser, Namespace, ArgumentTypeError
from datetime import date, datetime
from enum import Enum


class Operation(Enum):
    DOWNLOAD = "download"
    PARSE = "parse"


class ScriptArguments:
    def __init__(self):
        parser: ArgumentParser = ArgumentParser()
        parser.add_argument('operation')
        parser.add_argument('-d', '--creation-date', type=self.__valid_date)
        self.namespace: Namespace = parser.parse_args()

    def get_creation_date(self) -> date:
        return self.namespace.creation_date

    def get_operation(self) -> Operation:
        return Operation[self.namespace.operation.upper()]

    @staticmethod
    def __valid_date(s: str) -> date:
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            msg: str = f"Not a valid date: '{s}'. Expected format: YYYY-MM-DD."
            raise ArgumentTypeError(msg)
