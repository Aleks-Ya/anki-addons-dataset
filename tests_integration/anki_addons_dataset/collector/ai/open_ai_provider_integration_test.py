from pathlib import Path
from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText
from anki_addons_dataset.collector.ai.openai_ai_provider import OpenAiAiProvider
from anki_addons_dataset.common.data_types import AiModel


def test_response() -> None:
    endpoint: str = "https://api.openai.com/v1"
    api_key: str = Path("/home/aleks/.config/openai-api-key/api-key.txt").read_text().strip()
    model: AiModel = AiModel("gpt-5.6-luna")
    ai_provider: AiProvider = OpenAiAiProvider(endpoint, api_key, model)
    prompt: AiPrompt = AiPrompt("What is the capital of France?")
    answer: Optional[AiResponseText] = ai_provider.response(prompt)
    print(answer)
