import pytest

from anki_addons_dataset.collector.ai.ai_provider import AiPrompt
from anki_addons_dataset.collector.ai.no_ai_provider import NoAiProvider
from anki_addons_dataset.common.data_types import AiModel


def __provider() -> NoAiProvider:
    return NoAiProvider(AiModel("test-model"))


def test_response_must_not_be_called() -> None:
    provider: NoAiProvider = __provider()
    prompt: AiPrompt = AiPrompt("What is the capital of France?")

    with pytest.raises(AssertionError, match="NoAiProvider must not be called"):
        provider.response(prompt)


def test_verify_access_must_not_be_called() -> None:
    provider: NoAiProvider = __provider()

    with pytest.raises(AssertionError, match="NoAiProvider must not be called"):
        provider.verify_access()
