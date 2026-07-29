import pytest

from anki_addons_dataset.collector.collector_facade import CollectorFacade
from anki_addons_dataset.common.data_types import AddonInfos, ReportDate, ScriptVersion, SnapshotDate
from anki_addons_dataset.common.json_helper import JsonHelper
from anki_addons_dataset.common.working_dir import WorkingDir, SnapshotDir


def test_report_snapshots_generates_final_from_dump_without_raw(
        working_dir: WorkingDir, snapshot_dir: SnapshotDir, addon_infos: AddonInfos,
        script_version: ScriptVersion, report_date: ReportDate):
    # A 2-stage artifact that REPORT must not touch, and no 1-raw at all — proves decoupling from raw.
    stage_marker = snapshot_dir.get_stage_dir() / "marker.txt"
    stage_marker.write_text("keep me")
    JsonHelper.write_addon_infos_dump(addon_infos, script_version, snapshot_dir.get_addon_infos_dump())

    CollectorFacade(working_dir).report_snapshots(report_date)

    final_dir = snapshot_dir.get_final_dir()
    assert (final_dir / "json" / "data.json").exists()
    assert (final_dir / "json" / "aggregation.json").exists()
    assert snapshot_dir.get_metadata_json().exists()
    assert stage_marker.exists()
    assert not snapshot_dir.get_raw_dir().joinpath("1-anki-web").exists()


def test_report_snapshots_missing_dump_raises(
        working_dir: WorkingDir, snapshot_dir: SnapshotDir, report_date: ReportDate):
    with pytest.raises(FileNotFoundError, match="Run the 'parse' operation first"):
        CollectorFacade(working_dir).report_snapshots(report_date)


def test_report_snapshots_no_snapshots_is_noop(working_dir: WorkingDir, report_date: ReportDate):
    CollectorFacade(working_dir).report_snapshots(report_date)  # must not raise when history is empty
