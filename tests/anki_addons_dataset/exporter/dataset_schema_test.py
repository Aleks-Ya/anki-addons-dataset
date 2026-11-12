import dataclasses
import json
import types
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any, Union, get_args, get_origin, get_type_hints

import pyarrow
import pyarrow.parquet

from anki_addons_dataset.common.data_types import DATASET_VERSION, DatasetSnapshotMetadata, RawMetadata, \
    AiTagDefinition, AiTag, AiTagGroup, ReviewRow, AddonId, AddonReview, ReviewVote
from anki_addons_dataset.common.working_dir import SnapshotDir
from anki_addons_dataset.exporter.json_addon_info import Details
from anki_addons_dataset.exporter.parquet.parquet_exporter import ParquetExporter

SCHEMA_FILE: Path = Path(__file__).parents[3] / "docs" / "dataset" / "schema.json"
SCALAR_TYPES: dict[type, str] = {str: "string", int: "int64", float: "double", bool: "bool", date: "date32[day]"}


def __dataclass_columns(cls: type, prefix: str = "") -> dict[str, str]:
    columns: dict[str, str] = {}
    for name, hint in get_type_hints(cls).items():
        columns.update(__hint_columns(hint, f"{prefix}{name}"))
    return columns


def __hint_columns(hint: Any, path: str) -> dict[str, str]:
    if get_origin(hint) in (Union, types.UnionType):
        hint = next(arg for arg in get_args(hint) if arg is not type(None))
    while hasattr(hint, "__supertype__"):
        hint = hint.__supertype__
    if get_origin(hint) is list:
        return __hint_columns(get_args(hint)[0], f"{path}[]")
    if dataclasses.is_dataclass(hint):
        return __dataclass_columns(hint, f"{path}.")
    if isinstance(hint, type) and issubclass(hint, StrEnum):
        return {path: "string"}
    return {path: SCALAR_TYPES[hint]}


def __arrow_columns(arrow_type: pyarrow.DataType, path: str) -> dict[str, str]:
    if pyarrow.types.is_list(arrow_type) or pyarrow.types.is_large_list(arrow_type):
        return __arrow_columns(arrow_type.value_type, f"{path}[]")
    if pyarrow.types.is_struct(arrow_type):
        columns: dict[str, str] = {}
        for field in arrow_type:
            columns.update(__arrow_columns(field.type, f"{path}.{field.name}"))
        return columns
    return {path: "string" if pyarrow.types.is_large_string(arrow_type) else str(arrow_type)}


def __parquet_columns(file: Path) -> dict[str, str]:
    columns: dict[str, str] = {}
    for field in pyarrow.parquet.read_schema(file):
        columns.update(__arrow_columns(field.type, field.name))
    return columns


def __published_tables(snapshot_dir: SnapshotDir, dataset_snapshot_metadata: DatasetSnapshotMetadata,
                       raw_metadata: RawMetadata) -> dict[str, dict[str, str]]:
    final_dir: Path = snapshot_dir.get_final_dir()
    exporter: ParquetExporter = ParquetExporter(final_dir)
    exporter.export_tags([AiTagDefinition(AiTag("statistics"), AiTagGroup("function"), "Graphs")],
                         dataset_snapshot_metadata, raw_metadata)
    exporter.export_anki_versions([], dataset_snapshot_metadata, raw_metadata)
    exporter.export_reviews([ReviewRow(AddonId(1), AddonReview(ReviewVote.LIKE, date(2026, 1, 1), "Good", "Thanks"))])
    exporter.export_packages([])
    parquet_dir: Path = final_dir / "parquet"
    return {
        "data": __dataclass_columns(Details),
        "tags": __parquet_columns(parquet_dir / "tags.parquet"),
        "anki_versions": __parquet_columns(parquet_dir / "anki_versions.parquet"),
        "reviews": __parquet_columns(parquet_dir / "reviews.parquet"),
        "packages": __parquet_columns(parquet_dir / "packages.parquet"),
    }


def __changes(expected: dict[str, dict[str, str]], actual: dict[str, dict[str, str]]) -> tuple[list[str], list[str]]:
    added: list[str] = []
    broken: list[str] = []
    for table in sorted(expected.keys() | actual.keys()):
        if table not in actual:
            broken.append(f"table removed: {table}")
            continue
        if table not in expected:
            added.append(f"table added: {table}")
            continue
        for column in sorted(expected[table].keys() | actual[table].keys()):
            old, new = expected[table].get(column), actual[table].get(column)
            if old is None:
                added.append(f"{table}: added {column} ({new})")
            elif new is None:
                broken.append(f"{table}: removed {column} ({old})")
            elif old != new:
                broken.append(f"{table}: {column} changed from {old} to {new}")
    return added, broken


def test_published_schema_matches_the_dataset_version(snapshot_dir: SnapshotDir,
                                                      dataset_snapshot_metadata: DatasetSnapshotMetadata,
                                                      raw_metadata: RawMetadata):
    expected: dict[str, Any] = json.loads(SCHEMA_FILE.read_text())
    actual: dict[str, Any] = {
        "dataset_version": DATASET_VERSION,
        "tables": __published_tables(snapshot_dir, dataset_snapshot_metadata, raw_metadata),
    }
    if actual == expected:
        return
    added, broken = __changes(expected["tables"], actual["tables"])
    if added or broken:
        major, minor = (int(part) for part in expected["dataset_version"].split("."))
        required: str = f"{major + 1}.0" if broken else f"{major}.{minor + 1}"
        advice: str = (f"The published schema changed, so DATASET_VERSION must become {required} "
                       f"({'MAJOR: a breaking change' if broken else 'MINOR: an additive change'}) "
                       f"and docs/dataset/changelog.md needs an entry for it.")
        actual["dataset_version"] = required
    else:
        advice = f"DATASET_VERSION is {DATASET_VERSION}, but {SCHEMA_FILE.name} records {expected['dataset_version']}."
    changes: str = "\n".join(broken + added)
    raise AssertionError(f"{advice}\n{changes}\nThen write {SCHEMA_FILE} with:\n"
                         f"{json.dumps(actual, indent=2)}")
