from pathlib import Path
from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText
from anki_addons_dataset.collector.ai.deepseek_ai_provider import DeepSeekAiProvider
from anki_addons_dataset.common.data_types import AiModel


def test_response() -> None:
    endpoint: str = "https://api.deepseek.com"
    api_key: str = Path("/home/aleks/.config/anki-addons-dataset/deepseek-api-key.txt").read_text().strip()
    model: AiModel = AiModel("deepseek-flash")
    ai_provider: AiProvider = DeepSeekAiProvider(endpoint, api_key, model)
    prompt: AiPrompt = AiPrompt("What is the capital of France?")
    answer: Optional[AiResponseText] = ai_provider.response(prompt)
    print(answer)
