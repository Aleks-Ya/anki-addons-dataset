import logging
from datetime import datetime, timezone
from logging import Logger
from typing import Any, Optional
from urllib.parse import urlparse

import requests
from requests import Response

from anki_addons_dataset.collector.ai.ai_provider import AiPrompt, AiResponseText
from anki_addons_dataset.collector.ai.openai_ai_provider import OpenAiAiProvider

log: Logger = logging.getLogger(__name__)

PEAK_HOURS_DESCRIPTION: str = "01:00-04:00 and 06:00-10:00 UTC, Monday through Friday"


class DeepSeekAiProvider(OpenAiAiProvider):
    __domain: str = "deepseek.com"
    __balance_timeout_seconds: int = 30

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

    def verify_access(self) -> Optional[str]:
        super().verify_access()
        return self.__balance()

    def __balance(self) -> Optional[str]:
        url: str = f"{self._get_endpoint().rstrip('/')}/user/balance"
        response: Response = requests.get(url, headers={"Authorization": f"Bearer {self._get_api_key()}"},
                                          timeout=self.__balance_timeout_seconds)
        response.raise_for_status()
        balance: dict[str, Any] = response.json()
        if not balance.get("is_available"):
            raise PermissionError(f"DeepSeek balance is not available for API requests: {url}")
        balance_infos: list[dict[str, Any]] = balance.get("balance_infos") or []
        if not balance_infos:
            log.warning(f"DeepSeek reported no balance details: {balance}")
            return None
        balance_info: dict[str, Any] = balance_infos[0]
        return f"balance {balance_info.get('total_balance')} {balance_info.get('currency')}"
