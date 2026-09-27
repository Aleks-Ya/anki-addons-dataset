import logging
from datetime import datetime, timezone
from logging import Logger
from typing import Optional
from urllib.parse import urlparse

from anki_addons_dataset.collector.ai.ai_provider import AiPrompt, AiResponseText
from anki_addons_dataset.collector.ai.openai_ai_provider import OpenAiAiProvider

log: Logger = logging.getLogger(__name__)

PEAK_HOURS_DESCRIPTION: str = "01:00-04:00 and 06:00-10:00 UTC, Monday through Friday"


class DeepSeekAiProvider(OpenAiAiProvider):
    __domain: str = "deepseek.com"

    @staticmethod
    def owns(endpoint: str) -> bool:
        host: str = (urlparse(endpoint).hostname or "").lower()
        return host == DeepSeekAiProvider.__domain or host.endswith(f".{DeepSeekAiProvider.__domain}")

    @staticmethod
    def is_peak(now_utc: datetime) -> bool:
        return now_utc.weekday() < 5 and (1 <= now_utc.hour < 4 or 6 <= now_utc.hour < 10)

    def response(self, prompt: AiPrompt) -> Optional[AiResponseText]:
        now_utc: datetime = datetime.now(timezone.utc)
        if self.is_peak(now_utc):
            raise RuntimeError(f"DeepSeek peak hours ({PEAK_HOURS_DESCRIPTION}): "
                               f"it is {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC and the rate is double the "
                               f"off-peak one. Re-run the 'ai' operation outside the peak hours.")
        return super().response(prompt)
