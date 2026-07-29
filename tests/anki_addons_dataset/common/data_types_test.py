from datetime import date, datetime

from anki_addons_dataset.common.data_types import DatasetSnapshotMetadata, SnapshotDate, ReportDate, ScriptVersion


def test_dataset_snapshot_metadata_str():
    metadata: DatasetSnapshotMetadata = DatasetSnapshotMetadata(
        data_collection_date=SnapshotDate(date(2026, 7, 1)),
        report_generation_date=ReportDate(datetime(2026, 7, 29, 11, 39, 36)),
        script_version=ScriptVersion("1.3.0-SNAPSHOT"),
    )
    assert str(metadata) == ("DatasetSnapshotMetadata("
                             "data_collection_date=2026-07-01, "
                             "report_generation_date=2026-07-29 11:39:36, "
                             "script_version=1.3.0-SNAPSHOT)")
