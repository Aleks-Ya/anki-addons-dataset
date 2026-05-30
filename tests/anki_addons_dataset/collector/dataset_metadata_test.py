from datetime import date, datetime
from pathlib import Path
from textwrap import dedent

from anki_addons_dataset.collector.dataset_metadata import DatasetMetadata
from anki_addons_dataset.common.data_types import DatasetSnapshotMetadata, SnapshotDate, ReportDate
from anki_addons_dataset.common.working_dir import WorkingDir, SnapshotDir


def test_create_dataset_snapshot_metadata(working_dir: WorkingDir, report_date: ReportDate):
    script_version: str = "v0.0.1"
    snapshot_date: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-25"))
    snapshot_dir: SnapshotDir = working_dir.get_snapshot_dir(snapshot_date)
    exp_file: Path = snapshot_dir.get_path() / "metadata.json"
    assert not exp_file.exists()
    dataset_snapshot_metadata: DatasetSnapshotMetadata = DatasetMetadata.create_dataset_snapshot_metadata(
        snapshot_dir, script_version, report_date)
    DatasetMetadata.write_snapshot_metadata_to_json(snapshot_dir, dataset_snapshot_metadata)
    assert exp_file.read_text() == dedent(
        """\
        {
          "data_collection_date": "2025-01-25",
          "report_generation_date": "2026-04-25T14:25:45",
          "script_version": "v0.0.1"
        }"""
    )
