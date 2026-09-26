import logging
from logging import Logger

from openai import OpenAI
from openai.types.responses import Response

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText
from anki_addons_dataset.common.data_types import AiModel

log: Logger = logging.getLogger(__name__)


class OpenAiAiProvider(AiProvider):

    def __init__(self, endpoint: str, api_key: str, model: AiModel):
        super().__init__(model)
        self.__client: OpenAI = OpenAI(base_url=endpoint, api_key=api_key)

    def response(self, prompt: AiPrompt) -> AiResponseText:
        response: Response = self.__client.responses.create(
            model=self.get_model(),
            input=prompt
        )
        if response.status != "completed":
            raise ValueError(f"Response not completed: {response}")
        return AiResponseText(response.output_text)
