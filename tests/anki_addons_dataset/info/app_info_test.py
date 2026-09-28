import json
import logging
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from unittest.mock import Mock, MagicMock, patch

import httpx2
import pytest
from freezegun import freeze_time
from openai import APIStatusError
from pytest_mock import MockerFixture
from requests import Response

from anki_addons_dataset import __version__
from anki_addons_dataset.common.data_types import SnapshotDate, ReportDate, PageLoadTimeout, ElementWaitTimeout
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.config.app_config import AppConfig, AiConfig, GithubConfig
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient
from anki_addons_dataset.info.app_info import AppInfo

OFF_PEAK: str = "2026-09-28 12:00:00"


def __token_file(tmp_path: Path) -> Path:
    return tmp_path / ".github" / "token.txt"


def __write_token(tmp_path: Path) -> Path:
    token_file: Path = __token_file(tmp_path)
    token_file.parent.mkdir(parents=True)
    token_file.write_text("secret-token\n")
    return token_file


def __config(tmp_path: Path) -> AppConfig:
    defaults: AppConfig = AppConfig.defaults()
    return AppConfig(working_dir=tmp_path, github=GithubConfig(token_file=__token_file(tmp_path)),
                     ai=__ai_config(tmp_path), huggingface=defaults.huggingface, logging=defaults.logging,
                     sample=defaults.sample)


def __ai_config(tmp_path: Path, endpoint: str = "https://ai.example.com") -> AiConfig:
    defaults: AiConfig = AppConfig.defaults().ai
    return AiConfig(endpoint=endpoint, api_key_file=__ai_api_key_file(tmp_path), model=defaults.model,
                    readme_max_chars=defaults.readme_max_chars)


def __ai_api_key_file(tmp_path: Path) -> Path:
    return tmp_path / ".config" / "ai-api-key.txt"


def __write_ai_api_key(tmp_path: Path) -> Path:
    api_key_file: Path = __ai_api_key_file(tmp_path)
    api_key_file.parent.mkdir(parents=True, exist_ok=True)
    api_key_file.write_text("secret-ai-key\n")
    return api_key_file


def __ai_response() -> MagicMock:
    response: MagicMock = MagicMock()
    response.status = "completed"
    response.output_text = "pong"
    return response


def __patch_ai_api(side_effect: Optional[Exception] = None):
    client: MagicMock = MagicMock()
    if side_effect is None:
        client.responses.create.return_value = __ai_response()
    else:
        client.responses.create.side_effect = side_effect
    return patch("anki_addons_dataset.collector.ai.openai_ai_provider.OpenAI", return_value=client)


def __ai_status_error(status_code: int) -> APIStatusError:
    request: httpx2.Request = httpx2.Request("POST", "https://ai.example.com/responses")
    return APIStatusError("Authentication Fails",
                          response=httpx2.Response(status_code, request=request), body=None)


def __balance_response(payload: dict[str, Any]) -> Response:
    response: Response = Response()
    response.status_code = 200
    response._content = json.dumps(payload).encode("utf-8")
    return response


def __patch_deepseek_balance(payload: dict[str, Any]):
    return patch("anki_addons_dataset.collector.ai.deepseek_ai_provider.requests.get",
                 return_value=__balance_response(payload))


def __github_response(status_code: int) -> Response:
    response: Response = Response()
    response.status_code = status_code
    response.headers["x-ratelimit-remaining"] = "4999"
    return response


def __patch_github_api(status_code: int = 200):
    return patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
                 return_value=__github_response(status_code))


def __make_app_info(working_dir: WorkingDir, tmp_path: Path) -> AppInfo:
    return AppInfo(working_dir, __make_hugging_face_client(), __config(tmp_path),
                   PageLoadTimeout(90), ElementWaitTimeout(20))


def __make_deepseek_app_info(working_dir: WorkingDir, tmp_path: Path) -> AppInfo:
    config: AppConfig = replace(__config(tmp_path), ai=__ai_config(tmp_path, "https://api.deepseek.com"))
    return AppInfo(working_dir, __make_hugging_face_client(), config,
                   PageLoadTimeout(90), ElementWaitTimeout(20))


def __make_hugging_face_client() -> HuggingFaceClient:
    hugging_face_client: HuggingFaceClient = Mock()
    hugging_face_client.get_repo_id.return_value = "Ya-Alex/anki-addons"
    return hugging_face_client


def test_print_info(working_dir: WorkingDir, tmp_path: Path, caplog: pytest.LogCaptureFixture):
    app_info: AppInfo = __make_app_info(working_dir, tmp_path)
    snapshot_date: SnapshotDate = SnapshotDate(datetime(2026, 1, 1).date())
    report_date: ReportDate = ReportDate(datetime(2026, 1, 2, 3, 4, 5))
    token_file: Path = __write_token(tmp_path)
    api_key_file: Path = __write_ai_api_key(tmp_path)

    with caplog.at_level(logging.INFO):
        with __patch_github_api(), __patch_ai_api():
            app_info.print_info(snapshot_date, report_date)

    messages: str = "\n".join(record.message for record in caplog.records)
    assert f"Version: {__version__}" in messages
    assert "HuggingFace dataset: Ya-Alex/anki-addons" in messages
    assert str(working_dir.get_path()) in messages
    assert f"GitHub token file: {token_file}" in messages
    assert "secret-token" not in messages  # the token value itself is never logged
    assert "Snapshot date: 2026-01-01" in messages
    assert "Report date: 2026-01-02 03:04:05" in messages
    assert "Page load timeout: 90s" in messages
    assert "Element wait timeout: 20s" in messages
    assert f"GitHub token: OK ({token_file}, 4999 API requests remaining)" in messages
    assert f"AI key file: {api_key_file}" in messages
    assert "secret-ai-key" not in messages  # the key value itself is never logged
    assert f"AI API key: OK ({api_key_file})" in messages
    assert "AI provider: OK (https://ai.example.com, model deepseek-flash)" in messages
    assert "HuggingFace write access: OK (Ya-Alex/anki-addons)" in messages


def test_print_info_fails_without_github_token(working_dir: WorkingDir, tmp_path: Path,
                                               caplog: pytest.LogCaptureFixture):
    app_info: AppInfo = __make_app_info(working_dir, tmp_path)
    snapshot_date: SnapshotDate = SnapshotDate(datetime(2026, 1, 1).date())
    report_date: ReportDate = ReportDate(datetime(2026, 1, 2, 3, 4, 5))

    with caplog.at_level(logging.INFO):
        with pytest.raises(FileNotFoundError, match="Missing GitHub token file"):
            app_info.print_info(snapshot_date, report_date)

    messages: str = "\n".join(record.message for record in caplog.records)
    assert f"Version: {__version__}" in messages  # the config dump is printed before the failure
    assert f"GitHub token file: {tmp_path / '.github' / 'token.txt'}" in messages


def test_print_info_fails_when_github_rejects_the_token(working_dir: WorkingDir, tmp_path: Path,
                                                        caplog: pytest.LogCaptureFixture):
    app_info: AppInfo = __make_app_info(working_dir, tmp_path)
    snapshot_date: SnapshotDate = SnapshotDate(datetime(2026, 1, 1).date())
    report_date: ReportDate = ReportDate(datetime(2026, 1, 2, 3, 4, 5))
    __write_token(tmp_path)

    with caplog.at_level(logging.INFO):
        with __patch_github_api(401):
            with pytest.raises(PermissionError, match="GitHub rejected the token"):
                app_info.print_info(snapshot_date, report_date)

    # A present-but-invalid token is caught here rather than minutes later during `download`.
    messages: str = "\n".join(record.message for record in caplog.records)
    assert "GitHub token: OK" not in messages


def test_print_info_fails_without_hugging_face_access(working_dir: WorkingDir, tmp_path: Path,
                                                      caplog: pytest.LogCaptureFixture):
    hugging_face_client: HuggingFaceClient = Mock()
    hugging_face_client.get_repo_id.return_value = "Ya-Alex/anki-addons"
    hugging_face_client.verify_write_access.side_effect = PermissionError(
        "HuggingFace unauthorized: Ya-Alex/anki-addons")
    app_info: AppInfo = AppInfo(working_dir, hugging_face_client, __config(tmp_path),
                                PageLoadTimeout(90), ElementWaitTimeout(20))
    snapshot_date: SnapshotDate = SnapshotDate(datetime(2026, 1, 1).date())
    report_date: ReportDate = ReportDate(datetime(2026, 1, 2, 3, 4, 5))
    __write_token(tmp_path)
    __write_ai_api_key(tmp_path)

    with caplog.at_level(logging.INFO):
        with __patch_github_api(), __patch_ai_api():
            with pytest.raises(PermissionError, match="HuggingFace unauthorized"):
                app_info.print_info(snapshot_date, report_date)

    messages: str = "\n".join(record.message for record in caplog.records)
    assert "GitHub token: OK" in messages  # GitHub is verified first
    assert "HuggingFace write access: OK" not in messages


def test_print_info_fails_without_ai_api_key(working_dir: WorkingDir, tmp_path: Path,
                                             caplog: pytest.LogCaptureFixture):
    app_info: AppInfo = __make_app_info(working_dir, tmp_path)
    snapshot_date: SnapshotDate = SnapshotDate(datetime(2026, 1, 1).date())
    report_date: ReportDate = ReportDate(datetime(2026, 1, 2, 3, 4, 5))
    __write_token(tmp_path)

    with caplog.at_level(logging.INFO):
        with __patch_github_api():
            with pytest.raises(FileNotFoundError, match="Missing AI API key file"):
                app_info.print_info(snapshot_date, report_date)

    messages: str = "\n".join(record.message for record in caplog.records)
    assert "GitHub token: OK" in messages  # GitHub is verified first
    assert "HuggingFace write access: OK" not in messages


def test_print_info_fails_on_empty_ai_api_key(working_dir: WorkingDir, tmp_path: Path):
    app_info: AppInfo = __make_app_info(working_dir, tmp_path)
    __write_token(tmp_path)
    api_key_file: Path = __write_ai_api_key(tmp_path)
    api_key_file.write_text("  \n")

    snapshot_date: SnapshotDate = SnapshotDate(datetime(2026, 1, 1).date())
    report_date: ReportDate = ReportDate(datetime(2026, 1, 2, 3, 4, 5))

    with __patch_github_api():
        with pytest.raises(ValueError, match="Empty AI API key file"):
            app_info.print_info(snapshot_date, report_date)


def test_print_info_skips_hugging_face_check_when_github_token_missing(working_dir: WorkingDir, tmp_path: Path):
    hugging_face_client: HuggingFaceClient = Mock()
    hugging_face_client.get_repo_id.return_value = "Ya-Alex/anki-addons"
    app_info: AppInfo = AppInfo(working_dir, hugging_face_client, __config(tmp_path),
                                PageLoadTimeout(90), ElementWaitTimeout(20))
    snapshot_date: SnapshotDate = SnapshotDate(datetime(2026, 1, 1).date())
    report_date: ReportDate = ReportDate(datetime(2026, 1, 2, 3, 4, 5))

    with pytest.raises(FileNotFoundError, match="Missing GitHub token file"):
        app_info.print_info(snapshot_date, report_date)

    hugging_face_client.verify_write_access.assert_not_called()


def test_print_info_fails_when_the_ai_provider_rejects_the_key(working_dir: WorkingDir, tmp_path: Path,
                                                              caplog: pytest.LogCaptureFixture):
    hugging_face_client: HuggingFaceClient = __make_hugging_face_client()
    app_info: AppInfo = AppInfo(working_dir, hugging_face_client, __config(tmp_path),
                                PageLoadTimeout(90), ElementWaitTimeout(20))
    snapshot_date: SnapshotDate = SnapshotDate(datetime(2026, 1, 1).date())
    report_date: ReportDate = ReportDate(datetime(2026, 1, 2, 3, 4, 5))
    __write_token(tmp_path)
    __write_ai_api_key(tmp_path)

    with caplog.at_level(logging.INFO):
        with __patch_github_api(), __patch_ai_api(__ai_status_error(401)):
            with pytest.raises(APIStatusError):
                app_info.print_info(snapshot_date, report_date)

    messages: str = "\n".join(record.message for record in caplog.records)
    assert "AI API key: OK" in messages
    assert "AI provider: OK" not in messages
    hugging_face_client.verify_write_access.assert_not_called()


def test_print_info_fails_when_the_ai_provider_stays_silent(working_dir: WorkingDir, tmp_path: Path,
                                                            mocker: MockerFixture):
    app_info: AppInfo = __make_app_info(working_dir, tmp_path)
    snapshot_date: SnapshotDate = SnapshotDate(datetime(2026, 1, 1).date())
    report_date: ReportDate = ReportDate(datetime(2026, 1, 2, 3, 4, 5))
    __write_token(tmp_path)
    __write_ai_api_key(tmp_path)
    mocker.patch("anki_addons_dataset.collector.ai.openai_ai_provider.time.sleep")

    with __patch_github_api(), __patch_ai_api(ValueError("Service Unavailable")):
        with pytest.raises(RuntimeError, match="AI provider did not answer"):
            app_info.print_info(snapshot_date, report_date)


def test_print_info_reports_the_deepseek_balance(working_dir: WorkingDir, tmp_path: Path,
                                                 caplog: pytest.LogCaptureFixture):
    app_info: AppInfo = __make_deepseek_app_info(working_dir, tmp_path)
    snapshot_date: SnapshotDate = SnapshotDate(datetime(2026, 1, 1).date())
    report_date: ReportDate = ReportDate(datetime(2026, 1, 2, 3, 4, 5))
    __write_token(tmp_path)
    __write_ai_api_key(tmp_path)
    balance: dict[str, Any] = {"is_available": True,
                               "balance_infos": [{"currency": "USD", "total_balance": "12.34"}]}

    with caplog.at_level(logging.INFO):
        with __patch_github_api(), __patch_ai_api(), __patch_deepseek_balance(balance), freeze_time(OFF_PEAK):
            app_info.print_info(snapshot_date, report_date)

    messages: str = "\n".join(record.message for record in caplog.records)
    assert "AI provider: OK (https://api.deepseek.com, model deepseek-flash, balance 12.34 USD)" in messages


def test_print_info_fails_on_an_unavailable_deepseek_balance(working_dir: WorkingDir, tmp_path: Path):
    app_info: AppInfo = __make_deepseek_app_info(working_dir, tmp_path)
    snapshot_date: SnapshotDate = SnapshotDate(datetime(2026, 1, 1).date())
    report_date: ReportDate = ReportDate(datetime(2026, 1, 2, 3, 4, 5))
    __write_token(tmp_path)
    __write_ai_api_key(tmp_path)

    with __patch_github_api(), __patch_ai_api(), __patch_deepseek_balance({"is_available": False}), \
            freeze_time(OFF_PEAK):
        with pytest.raises(PermissionError, match="DeepSeek balance is not available"):
            app_info.print_info(snapshot_date, report_date)
