import logging
import time
from logging import Logger
from typing import Optional

from openai import OpenAI, APIStatusError
from openai.types.responses import Response

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText
from anki_addons_dataset.common.data_types import AiModel

log: Logger = logging.getLogger(__name__)


class OpenAiAiProvider(AiProvider):
    __max_attempts: int = 3
    __fatal_status_codes: frozenset[int] = frozenset({401, 402, 403})
    __retry_delay_seconds: int = 5
    __timeout_seconds: int = 120

    def __init__(self, endpoint: str, api_key: str, model: AiModel):
        super().__init__(model)
        self.__client: OpenAI = OpenAI(base_url=endpoint, api_key=api_key, timeout=self.__timeout_seconds)

    def response(self, prompt: AiPrompt) -> Optional[AiResponseText]:
        """Returns None once the retries are exhausted: one unanswered addon must not abort a whole run.

        Raises on a status no retry can fix (bad key, empty balance): every later addon would fail alike."""
        for attempt in range(1, self.__max_attempts + 1):
            try:
                response: Response = self.__client.responses.create(
                    model=self.get_model(),
                    input=prompt
                )
                if response.status != "completed":
                    raise ValueError(f"Response not completed: {response}")
                return AiResponseText(response.output_text)
            except Exception as e:
                if self.__is_fatal(e):
                    log.error(f"AI request rejected and not retryable: {e}", exc_info=True)
                    raise
                if attempt == self.__max_attempts:
                    log.error(f"AI request failed after {attempt} attempts: {e}", exc_info=True)
                    return None
                delay: int = self.__retry_delay_seconds * attempt
                log.warning(f"AI request failed (attempt {attempt}/{self.__max_attempts}), "
                            f"retrying in {delay}s: {e}")
                time.sleep(delay)
        return None

    @staticmethod
    def __is_fatal(error: Exception) -> bool:
        return isinstance(error, APIStatusError) \
            and error.status_code in OpenAiAiProvider.__fatal_status_codes
