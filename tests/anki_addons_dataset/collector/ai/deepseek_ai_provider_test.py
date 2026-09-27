from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture

from anki_addons_dataset.collector.ai.ai_enricher import AiEnricher
from anki_addons_dataset.collector.ai.ai_provider import AiPrompt, AiResponseText
from anki_addons_dataset.collector.ai.ai_summarizer import AiSummarizer
from anki_addons_dataset.collector.ai.cached_ai_provider import CachedAiProvider
from anki_addons_dataset.collector.ai.deepseek_ai_provider import DeepSeekAiProvider
from anki_addons_dataset.collector.ai.openai_ai_provider import OpenAiAiProvider
from anki_addons_dataset.common.data_types import AddonInfo, AddonInfos, AiModel

MODEL: AiModel = AiModel("deepseek-flash")
PROMPT: AiPrompt = AiPrompt("What is the capital of France?")

MONDAY: str = "2026-09-28"
SATURDAY: str = "2026-10-03"
SUNDAY: str = "2026-10-04"


def __provider() -> DeepSeekAiProvider:
    return DeepSeekAiProvider("https://api.deepseek.com", "api-key", MODEL)


def __utc(day: str, time: str) -> datetime:
    return datetime.fromisoformat(f"{day}T{time}").replace(tzinfo=timezone.utc)


@pytest.mark.parametrize("time", ["00:59:59", "04:00:00", "05:59:59", "10:00:00", "23:59:59"])
def test_weekday_off_peak_hours(time: str) -> None:
    assert DeepSeekAiProvider.is_peak(__utc(MONDAY, time)) is False


@pytest.mark.parametrize("time", ["01:00:00", "03:59:59", "06:00:00", "09:59:59"])
def test_weekday_peak_hours(time: str) -> None:
    assert DeepSeekAiProvider.is_peak(__utc(MONDAY, time)) is True


@pytest.mark.parametrize("day", [SATURDAY, SUNDAY])
@pytest.mark.parametrize("time", ["01:00:00", "09:59:59"])
def test_weekend_is_never_peak(day: str, time: str) -> None:
    assert DeepSeekAiProvider.is_peak(__utc(day, time)) is False


@pytest.mark.parametrize("endpoint", ["https://api.deepseek.com", "https://api.deepseek.com/",
                                      "https://API.DeepSeek.COM/v1", "https://deepseek.com",
                                      "https://api.deepseek.com:443"])
def test_owns_deepseek_endpoints(endpoint: str) -> None:
    assert DeepSeekAiProvider.owns(endpoint) is True


@pytest.mark.parametrize("endpoint", ["https://api.openai.com/v1", "https://deepseek.com.example.org",
                                      "https://notdeepseek.com", ""])
def test_does_not_own_other_endpoints(endpoint: str) -> None:
    assert DeepSeekAiProvider.owns(endpoint) is False


@freeze_time(f"{MONDAY} 06:30:00")
def test_response_fails_during_peak_hours(mocker: MockerFixture) -> None:
    super_response = mocker.patch.object(OpenAiAiProvider, "response")
    provider: DeepSeekAiProvider = __provider()

    with pytest.raises(RuntimeError, match="peak hours"):
        provider.response(PROMPT)

    super_response.assert_not_called()


@freeze_time(f"{MONDAY} 12:30:00")
def test_response_delegates_outside_peak_hours(mocker: MockerFixture) -> None:
    super_response = mocker.patch.object(OpenAiAiProvider, "response",
                                         return_value=AiResponseText("Paris"))

    answer: Optional[AiResponseText] = __provider().response(PROMPT)

    assert answer == "Paris"
    super_response.assert_called_once_with(PROMPT)


@freeze_time(f"{MONDAY} 06:30:00")
def test_peak_hours_abort_the_whole_enrichment(addon_info: AddonInfo, tmp_path: Path) -> None:
    cache_file: Path = tmp_path / "4-ai" / "ai-cache.jsonl"
    provider: CachedAiProvider = CachedAiProvider(__provider(), cache_file)
    enricher: AiEnricher = AiEnricher(AiSummarizer(provider, readme_max_chars=8000), MODEL)

    addon_infos: AddonInfos = AddonInfos([addon_info])

    with pytest.raises(RuntimeError, match=f"Cannot summarize addon: {addon_info.header.id}") as exc_info:
        enricher.enrich(addon_infos)

    assert "peak hours" in str(exc_info.value.__cause__)
    assert not cache_file.exists()
