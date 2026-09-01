import logging
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from anki_addons_dataset import __version__
from anki_addons_dataset.common.data_types import SnapshotDate, ReportDate
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient
from anki_addons_dataset.info.app_info import AppInfo


def __make_app_info(working_dir: WorkingDir) -> AppInfo:
    hugging_face_client: HuggingFaceClient = Mock()
    hugging_face_client.get_repo_id.return_value = "Ya-Alex/anki-addons"
    return AppInfo(working_dir, hugging_face_client)


def test_print_info(working_dir: WorkingDir, tmp_path: Path, caplog: pytest.LogCaptureFixture):
    app_info: AppInfo = __make_app_info(working_dir)
    snapshot_date: SnapshotDate = SnapshotDate(datetime(2026, 1, 1).date())
    report_date: ReportDate = ReportDate(datetime(2026, 1, 2, 3, 4, 5))
    token_dir: Path = tmp_path / ".github"
    token_dir.mkdir(parents=True)
    token_file: Path = token_dir / "token.txt"
    token_file.write_text("secret-token\n")

    with caplog.at_level(logging.INFO):
        with patch.object(Path, "home", return_value=tmp_path):
            app_info.print_info(snapshot_date, report_date)

    messages: str = "\n".join(record.message for record in caplog.records)
    assert f"Version: {__version__}" in messages
    assert "HuggingFace dataset: Ya-Alex/anki-addons" in messages
    assert str(working_dir.get_path()) in messages
    assert f"GitHub token file: {token_file}" in messages
    assert "secret-token" not in messages  # the token value itself is never logged
    assert "Snapshot date: 2026-01-01" in messages
    assert "Report date: 2026-01-02 03:04:05" in messages


def test_print_info_fails_without_github_token(working_dir: WorkingDir, tmp_path: Path,
                                               caplog: pytest.LogCaptureFixture):
    app_info: AppInfo = __make_app_info(working_dir)
    snapshot_date: SnapshotDate = SnapshotDate(datetime(2026, 1, 1).date())
    report_date: ReportDate = ReportDate(datetime(2026, 1, 2, 3, 4, 5))

    with caplog.at_level(logging.INFO):
        with patch.object(Path, "home", return_value=tmp_path):
            with pytest.raises(FileNotFoundError, match="Missing GitHub token file"):
                app_info.print_info(snapshot_date, report_date)

    messages: str = "\n".join(record.message for record in caplog.records)
    assert f"Version: {__version__}" in messages  # the config dump is printed before the failure
    assert f"GitHub token file: {tmp_path / '.github' / 'token.txt'}" in messages
