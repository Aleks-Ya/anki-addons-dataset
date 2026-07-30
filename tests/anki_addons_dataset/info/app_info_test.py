import logging
from datetime import datetime
from unittest.mock import Mock

from pytest import LogCaptureFixture

from anki_addons_dataset import __version__
from anki_addons_dataset.common.data_types import SnapshotDate, ReportDate
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient
from anki_addons_dataset.info.app_info import AppInfo


def test_print_info(working_dir: WorkingDir, caplog: LogCaptureFixture):
    hugging_face_client: HuggingFaceClient = Mock()
    hugging_face_client.get_repo_id.return_value = "Ya-Alex/anki-addons"
    app_info: AppInfo = AppInfo(working_dir, hugging_face_client)
    snapshot_date: SnapshotDate = SnapshotDate(datetime(2026, 1, 1).date())
    report_date: ReportDate = ReportDate(datetime(2026, 1, 2, 3, 4, 5))

    with caplog.at_level(logging.INFO):
        app_info.print_info(snapshot_date, report_date)

    messages: str = "\n".join(record.message for record in caplog.records)
    assert f"Version: {__version__}" in messages
    assert "HuggingFace dataset: Ya-Alex/anki-addons" in messages
    assert str(working_dir.get_path()) in messages
    assert "Snapshot date: 2026-01-01" in messages
    assert "Report date: 2026-01-02 03:04:05" in messages
