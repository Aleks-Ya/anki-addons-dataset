from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText


def test_response(ai_provider: AiProvider) -> None:
    prompt: AiPrompt = AiPrompt("What is the capital of France?")
    answer: Optional[AiResponseText] = ai_provider.response(prompt)
    print(answer)
    assert answer is not None
