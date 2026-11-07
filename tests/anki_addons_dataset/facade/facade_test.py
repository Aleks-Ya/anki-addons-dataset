from datetime import date
from typing import Optional
from unittest.mock import Mock, call, patch

from anki_addons_dataset.argument.script_arguments import Operation
from anki_addons_dataset.collector.collector_facade import CollectorFacade
from anki_addons_dataset.common.data_types import ReportDate, SnapshotDate
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.facade.facade import Facade


def test_process(facade: Facade):
    assert facade is not None


def test_ai_operation_summarizes_snapshots(facade: Facade, report_date: ReportDate):
    snapshot_date: Optional[SnapshotDate] = None

    with patch.object(CollectorFacade, "summarize_snapshots") as summarize_snapshots:
        facade.process(Operation.AI, snapshot_date, report_date)

    summarize_snapshots.assert_called_once_with(None)


def test_ai_operation_passes_the_snapshot_date_on(facade: Facade, report_date: ReportDate):
    snapshot_date: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))

    with patch.object(CollectorFacade, "summarize_snapshots") as summarize_snapshots:
        facade.process(Operation.AI, snapshot_date, report_date)

    summarize_snapshots.assert_called_once_with(snapshot_date)


def test_parse_operation_parses_snapshots(facade: Facade, report_date: ReportDate):
    snapshot_date: Optional[SnapshotDate] = None

    with patch.object(CollectorFacade, "parse_snapshots") as parse_snapshots:
        facade.process(Operation.PARSE, snapshot_date, report_date)

    parse_snapshots.assert_called_once_with(None)


def test_parse_operation_passes_the_snapshot_date_on(facade: Facade, report_date: ReportDate):
    snapshot_date: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))

    with patch.object(CollectorFacade, "parse_snapshots") as parse_snapshots:
        facade.process(Operation.PARSE, snapshot_date, report_date)

    parse_snapshots.assert_called_once_with(snapshot_date)


def test_report_operation_reports_snapshots(facade: Facade, report_date: ReportDate):
    snapshot_date: Optional[SnapshotDate] = None

    with patch.object(CollectorFacade, "report_snapshots") as report_snapshots:
        facade.process(Operation.REPORT, snapshot_date, report_date)

    report_snapshots.assert_called_once_with(None, report_date)


def test_report_operation_passes_the_snapshot_date_on(facade: Facade, report_date: ReportDate):
    snapshot_date: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))

    with patch.object(CollectorFacade, "report_snapshots") as report_snapshots:
        facade.process(Operation.REPORT, snapshot_date, report_date)

    report_snapshots.assert_called_once_with(snapshot_date, report_date)


def test_download_operation_downloads_the_snapshot(facade: Facade, report_date: ReportDate):
    snapshot_date: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))

    with patch.object(CollectorFacade, "download_snapshot") as download_snapshot:
        facade.process(Operation.DOWNLOAD, snapshot_date, report_date)

    download_snapshot.assert_called_once_with(snapshot_date)


def test_info_operation_prints_the_info(facade: Facade, report_date: ReportDate):
    snapshot_date: SnapshotDate = SnapshotDate(date.fromisoformat("2025-01-01"))

    with patch("anki_addons_dataset.facade.facade.AppInfo") as app_info:
        facade.process(Operation.INFO, snapshot_date, report_date)

    app_info.return_value.print_info.assert_called_once_with(snapshot_date, report_date)


def test_init_operation_initializes_the_working_dir(facade: Facade, report_date: ReportDate):
    with patch("anki_addons_dataset.facade.facade.WorkingDirInitializer") as initializer:
        facade.process(Operation.INIT, None, report_date)

    initializer.return_value.initialize_working_dir.assert_called_once_with()


def test_bundle_operation_creates_the_bundle(facade: Facade, working_dir: WorkingDir, report_date: ReportDate):
    with patch("anki_addons_dataset.facade.facade.DatasetBundle") as dataset_bundle:
        facade.process(Operation.BUNDLE, None, report_date)

    dataset_bundle.assert_called_once_with(working_dir)
    dataset_bundle.return_value.create_bundle.assert_called_once_with()


def test_upload_operation_tags_a_backup_then_uploads_then_prunes(
        facade: Facade, working_dir: WorkingDir, hugging_face_client: Mock, report_date: ReportDate):
    facade.process(Operation.UPLOAD, None, report_date)

    bundle_dir = working_dir.get_bundle_dir()
    assert hugging_face_client.method_calls == [
        call.tag_backup(), call.upload_dataset(bundle_dir), call.prune_orphans(bundle_dir)]
