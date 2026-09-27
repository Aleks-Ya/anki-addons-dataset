from datetime import date
from typing import Optional
from unittest.mock import patch

from anki_addons_dataset.argument.script_arguments import Operation
from anki_addons_dataset.collector.collector_facade import CollectorFacade
from anki_addons_dataset.common.data_types import ReportDate, SnapshotDate
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
