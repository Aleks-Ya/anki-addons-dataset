import dataclasses
import types
from datetime import date
from enum import StrEnum
from typing import Any, Union, get_args, get_origin, get_type_hints

import pyarrow


class ArrowSchema:
    __scalar_types: dict[type, pyarrow.DataType] = {
        str: pyarrow.string(), int: pyarrow.int64(), float: pyarrow.float64(), bool: pyarrow.bool_(),
        date: pyarrow.date32()}

    @staticmethod
    def of(cls: type) -> pyarrow.Schema:
        return pyarrow.schema(ArrowSchema.__fields(cls))

    @staticmethod
    def __fields(cls: type) -> list[pyarrow.Field]:
        return [pyarrow.field(name, ArrowSchema.__type(hint, f"{cls.__name__}.{name}"))
                for name, hint in get_type_hints(cls).items()]

    @staticmethod
    def __type(hint: Any, path: str) -> pyarrow.DataType:
        if get_origin(hint) in (Union, types.UnionType):
            hint = next(arg for arg in get_args(hint) if arg is not type(None))
        while hasattr(hint, "__supertype__"):
            hint = hint.__supertype__
        if get_origin(hint) is list:
            return pyarrow.list_(ArrowSchema.__type(get_args(hint)[0], f"{path}[]"))
        if dataclasses.is_dataclass(hint) and isinstance(hint, type):
            return pyarrow.struct(ArrowSchema.__fields(hint))
        if isinstance(hint, type) and issubclass(hint, StrEnum):
            return pyarrow.string()
        if hint in ArrowSchema.__scalar_types:
            return ArrowSchema.__scalar_types[hint]
        raise TypeError(f"No Arrow type for {path}: {hint}")
