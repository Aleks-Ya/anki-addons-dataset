from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText


def test_response(ai_provider: AiProvider) -> None:
    prompt: AiPrompt = AiPrompt("What is the capital of France?")
    answer: Optional[AiResponseText] = ai_provider.response(prompt)
    print(answer)
    assert answer is not None


def test_verify_access(ai_provider: AiProvider) -> None:
    details: Optional[str] = ai_provider.verify_access()
    print(details)
