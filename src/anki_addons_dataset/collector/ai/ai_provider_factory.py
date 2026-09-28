from anki_addons_dataset.collector.ai.ai_provider import AiProvider
from anki_addons_dataset.collector.ai.deepseek_ai_provider import DeepSeekAiProvider
from anki_addons_dataset.collector.ai.no_ai_provider import NoAiProvider
from anki_addons_dataset.collector.ai.openai_ai_provider import OpenAiAiProvider
from anki_addons_dataset.common.data_types import AiModel
from anki_addons_dataset.config.app_config import AiConfig


class AiProviderFactory:

    @staticmethod
    def create(ai_config: AiConfig, offline: bool) -> AiProvider:
        model: AiModel = AiModel(ai_config.model)
        if offline:
            return NoAiProvider(model)
        online_provider_type: type[OpenAiAiProvider] = \
            DeepSeekAiProvider if DeepSeekAiProvider.owns(ai_config.endpoint) else OpenAiAiProvider
        return online_provider_type(ai_config.endpoint, ai_config.api_key_file.read_text().strip(), model)
