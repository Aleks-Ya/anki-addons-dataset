import logging
from logging import Logger

from anki_addons_dataset.collector.ai.openai_ai_provider import OpenAiAiProvider
from anki_addons_dataset.common.data_types import AiModel

log: Logger = logging.getLogger(__name__)


class DeepSeekAiProvider(OpenAiAiProvider):

    def __init__(self, endpoint: str, api_key: str, model: AiModel):
        super().__init__(endpoint, api_key, model)
