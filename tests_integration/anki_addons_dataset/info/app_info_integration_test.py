import logging
from datetime import datetime

import pytest

from anki_addons_dataset.common.data_types import ElementWaitTimeout, PageLoadTimeout, ReportDate, SnapshotDate
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.config.app_config import AppConfig
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient
from anki_addons_dataset.info.app_info import AppInfo


def test_print_info(working_dir: WorkingDir, hugging_face_client: HuggingFaceClient, integration_config: AppConfig,
                    snapshot_date: SnapshotDate, page_load_timeout: PageLoadTimeout,
                    element_wait_timeout: ElementWaitTimeout, caplog: pytest.LogCaptureFixture) -> None:
    app_info: AppInfo = AppInfo(
        working_dir, hugging_face_client, integration_config, page_load_timeout, element_wait_timeout)

    with caplog.at_level(logging.INFO):
        app_info.print_info(snapshot_date, ReportDate(datetime.now()))

    assert "GitHub token: OK" in caplog.text
    assert "HuggingFace write access: OK" in caplog.text
