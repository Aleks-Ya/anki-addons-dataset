from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import NewType, Optional

import pyarrow
import pytest

from anki_addons_dataset.exporter.parquet.arrow_schema import ArrowSchema

Title = NewType("Title", str)


class Color(StrEnum):
    RED = "red"


@dataclass
class Inner:
    name: str
    size: Optional[int]


@dataclass
class Outer:
    id: int
    title: Title
    color: Color
    score: float | None
    active: bool
    day: date
    inner: Optional[Inner]
    inners: list[Inner]
    tags: Optional[list[str]]


@dataclass
class Unsupported:
    moment: datetime


def test_of_maps_every_supported_type():
    inner: pyarrow.DataType = pyarrow.struct([("name", pyarrow.string()), ("size", pyarrow.int64())])
    assert ArrowSchema.of(Outer) == pyarrow.schema([
        ("id", pyarrow.int64()), ("title", pyarrow.string()), ("color", pyarrow.string()),
        ("score", pyarrow.float64()), ("active", pyarrow.bool_()), ("day", pyarrow.date32()), ("inner", inner),
        ("inners", pyarrow.list_(inner)), ("tags", pyarrow.list_(pyarrow.string()))])


def test_of_rejects_an_unsupported_type():
    with pytest.raises(TypeError, match="Unsupported.moment"):
        ArrowSchema.of(Unsupported)
