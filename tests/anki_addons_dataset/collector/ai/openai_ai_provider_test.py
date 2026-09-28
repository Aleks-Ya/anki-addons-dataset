from typing import Optional
from unittest.mock import MagicMock

import httpx2
import pytest
from openai import APIStatusError
from pytest_mock import MockerFixture

from anki_addons_dataset.collector.ai.ai_provider import AiPrompt, AiResponseText
from anki_addons_dataset.collector.ai.openai_ai_provider import OpenAiAiProvider
from anki_addons_dataset.common.data_types import AiModel

MODEL: AiModel = AiModel("gpt-flash")
PROMPT: AiPrompt = AiPrompt("What is the capital of France?")
MAX_ATTEMPTS: int = 3


@pytest.fixture
def sleep(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("anki_addons_dataset.collector.ai.openai_ai_provider.time.sleep")


@pytest.fixture
def create(mocker: MockerFixture) -> MagicMock:
    client: MagicMock = mocker.patch(
        "anki_addons_dataset.collector.ai.openai_ai_provider.OpenAI").return_value
    return client.responses.create


def __provider() -> OpenAiAiProvider:
    return OpenAiAiProvider("https://api.openai.com/v1", "api-key", MODEL)


def __response(status: str = "completed", output_text: str = "Paris") -> MagicMock:
    response: MagicMock = MagicMock()
    response.status = status
    response.output_text = output_text
    return response


def __status_error(status_code: int) -> APIStatusError:
    request: httpx2.Request = httpx2.Request("POST", "https://api.openai.com/v1/responses")
    return APIStatusError("Insufficient Balance",
                          response=httpx2.Response(status_code, request=request), body=None)


def test_response_returns_output_text(create: MagicMock, sleep: MagicMock) -> None:
    create.return_value = __response()

    answer: Optional[AiResponseText] = __provider().response(PROMPT)

    assert answer == "Paris"
    assert create.call_count == 1
    sleep.assert_not_called()


@pytest.mark.parametrize("status_code", [401, 402, 403])
def test_fatal_status_fails_without_retry(status_code: int, create: MagicMock, sleep: MagicMock) -> None:
    create.side_effect = __status_error(status_code)
    provider: OpenAiAiProvider = __provider()

    with pytest.raises(APIStatusError):
        provider.response(PROMPT)

    assert create.call_count == 1
    sleep.assert_not_called()


@pytest.mark.parametrize("error", [__status_error(500), __status_error(429), ValueError("boom")])
def test_transient_error_is_retried(error: Exception, create: MagicMock, sleep: MagicMock) -> None:
    create.side_effect = error

    answer: Optional[AiResponseText] = __provider().response(PROMPT)

    assert answer is None
    assert create.call_count == MAX_ATTEMPTS
    assert sleep.call_count == MAX_ATTEMPTS - 1


def test_incomplete_response_is_retried(create: MagicMock, sleep: MagicMock) -> None:
    create.return_value = __response(status="incomplete")

    answer: Optional[AiResponseText] = __provider().response(PROMPT)

    assert answer is None
    assert create.call_count == MAX_ATTEMPTS
    assert sleep.call_count == MAX_ATTEMPTS - 1


def test_retry_succeeds_after_transient_error(create: MagicMock, sleep: MagicMock) -> None:
    create.side_effect = [__status_error(500), __response()]

    answer: Optional[AiResponseText] = __provider().response(PROMPT)

    assert answer == "Paris"
    assert create.call_count == 2
    assert sleep.call_count == 1


def test_verify_access_asks_for_one_answer(create: MagicMock, sleep: MagicMock) -> None:
    create.return_value = __response(output_text="pong")

    details: Optional[str] = __provider().verify_access()

    assert details is None
    assert create.call_count == 1
    assert create.call_args.kwargs["model"] == MODEL
    sleep.assert_not_called()


@pytest.mark.parametrize("status_code", [401, 402, 403])
def test_verify_access_fails_on_a_fatal_status(status_code: int, create: MagicMock, sleep: MagicMock) -> None:
    create.side_effect = __status_error(status_code)
    provider: OpenAiAiProvider = __provider()

    with pytest.raises(APIStatusError):
        provider.verify_access()

    assert create.call_count == 1
    sleep.assert_not_called()


def test_verify_access_fails_when_the_retries_are_exhausted(create: MagicMock, sleep: MagicMock) -> None:
    create.side_effect = ValueError("boom")
    provider: OpenAiAiProvider = __provider()

    with pytest.raises(RuntimeError, match="AI provider did not answer: https://api.openai.com/v1, model gpt-flash"):
        provider.verify_access()

    assert create.call_count == MAX_ATTEMPTS
