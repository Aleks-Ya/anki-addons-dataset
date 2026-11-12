import json
from pathlib import Path
from typing import Any

import pyarrow
import pyarrow.parquet

from anki_addons_dataset.common.data_types import DATASET_VERSION, DatasetSnapshotMetadata, RawMetadata, \
    AiTagDefinition, AiTag, AiTagGroup, AddonInfos
from anki_addons_dataset.common.working_dir import SnapshotDir
from anki_addons_dataset.exporter.parquet.parquet_exporter import ParquetExporter

SCHEMA_FILE: Path = Path(__file__).parents[3] / "docs" / "dataset" / "schema.json"


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
    exporter.export_addon_infos(AddonInfos([]), dataset_snapshot_metadata, raw_metadata)
    exporter.export_tags([AiTagDefinition(AiTag("statistics"), AiTagGroup("function"), "Graphs")],
                         dataset_snapshot_metadata, raw_metadata)
    exporter.export_anki_versions([], dataset_snapshot_metadata, raw_metadata)
    exporter.export_reviews([])
    exporter.export_packages([])
    parquet_dir: Path = final_dir / "parquet"
    return {
        "data": __parquet_columns(parquet_dir / "data.parquet"),
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
