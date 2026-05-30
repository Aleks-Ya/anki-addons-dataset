from datetime import date, datetime
from pathlib import Path
from textwrap import dedent

from anki_addons_dataset.collector.dataset_metadata import DatasetMetadata
from anki_addons_dataset.common.data_types import DatasetVersionMetadata, SnapshotDate, ReportDate
from anki_addons_dataset.common.working_dir import WorkingDir, VersionDir


def test_create_dataset_version_metadata(working_dir: WorkingDir, report_date: ReportDate):
    script_version: str = "v0.0.1"
    snapshot_date: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-25"))
    version_dir: VersionDir = working_dir.get_version_dir(snapshot_date)
    exp_file: Path = version_dir.get_path() / "metadata.json"
    assert not exp_file.exists()
    dataset_version_metadata: DatasetVersionMetadata = DatasetMetadata.create_dataset_version_metadata(
        version_dir, script_version, report_date)
    DatasetMetadata.write_version_metadata_to_json(version_dir, dataset_version_metadata)
    assert exp_file.read_text() == dedent(
        """\
        {
          "data_collection_date": "2025-01-25",
          "report_generation_date": "2026-04-25T14:25:45",
          "script_version": "v0.0.1"
        }"""
    )
