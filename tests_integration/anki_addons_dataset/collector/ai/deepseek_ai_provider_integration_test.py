from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText
from anki_addons_dataset.collector.ai.deepseek_ai_provider import DeepSeekAiProvider
from anki_addons_dataset.common.data_types import AiModel
from anki_addons_dataset.config.app_config import AppConfig


def test_response(integration_config: AppConfig, ai_model: AiModel) -> None:
    api_key: str = integration_config.ai.api_key_file.read_text().strip()
    ai_provider: AiProvider = DeepSeekAiProvider(integration_config.ai.endpoint, api_key, ai_model)
    prompt: AiPrompt = AiPrompt("What is the capital of France?")
    answer: Optional[AiResponseText] = ai_provider.response(prompt)
    print(answer)
    assert answer is not None
