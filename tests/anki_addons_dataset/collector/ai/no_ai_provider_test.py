import pytest

from anki_addons_dataset.collector.ai.ai_provider import AiPrompt
from anki_addons_dataset.collector.ai.no_ai_provider import NoAiProvider
from anki_addons_dataset.common.data_types import AiModel


def __provider() -> NoAiProvider:
    return NoAiProvider(AiModel("test-model"))


def test_response_must_not_be_called() -> None:
    with pytest.raises(AssertionError, match="NoAiProvider must not be called"):
        __provider().response(AiPrompt("What is the capital of France?"))


def test_verify_access_must_not_be_called() -> None:
    with pytest.raises(AssertionError, match="NoAiProvider must not be called"):
        __provider().verify_access()
