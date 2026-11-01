import datetime
import time
from datetime import datetime
from threading import Lock
from typing import Any, Optional
import logging
from logging import Logger

from requests import Response
from requests.structures import CaseInsensitiveDict

log: Logger = logging.getLogger(__name__)


class GithubRateLimit:
    __limited_status_codes: tuple[int, ...] = (403, 429)
    __default_limited_wait_seconds: int = 60

    def __init__(self):
        self.__lock: Lock = Lock()
        self.__status_code: Optional[int] = None
        self.__retry_after: Optional[int] = None
        self.__retry_limit_remaining: Optional[int] = None
        self.__retry_limit_reset: Optional[int] = None

    def update_rate_limit(self, response: Response) -> None:
        with self.__lock:
            self.__update_rate_limit(response)

    def wait_for_reset(self) -> None:
        with self.__lock:
            self.__wait_for_reset()

    def get_limit_remaining(self) -> Optional[int]:
        with self.__lock:
            return self.__retry_limit_remaining

    def is_limited(self, response: Response) -> bool:
        if response.status_code not in self.__limited_status_codes:
            return False
        headers: CaseInsensitiveDict[str] = response.headers
        return (headers.get("x-ratelimit-remaining") == "0"
                or "retry-after" in headers
                or "rate limit" in response.text.lower())

    def wait_after_limited(self, response: Response) -> None:
        with self.__lock:
            sleep_time: int = max(1, self.__limited_wait_seconds(response))
            log.info(f"Rate limited (status {response.status_code}) at {response.url}. "
                     f"Waiting for {sleep_time} seconds")
            time.sleep(sleep_time)
            log.info("Done waiting after rate limit")

    def __limited_wait_seconds(self, response: Response) -> int:
        retry_after: Optional[str] = response.headers.get("retry-after")
        if retry_after:
            return int(retry_after)
        retry_limit_reset: Optional[str] = response.headers.get("x-ratelimit-reset")
        if retry_limit_reset:
            return int(retry_limit_reset) - int(round(time.time()))
        return self.__default_limited_wait_seconds

    def __update_rate_limit(self, response: Response) -> None:
        self.__status_code = response.status_code
        headers: CaseInsensitiveDict[str] = response.headers
        retry_after: Optional[str] = headers.get("retry-after")
        retry_limit_remaining: Optional[str] = headers.get("x-ratelimit-remaining")
        retry_limit_reset: Optional[str] = headers.get("x-ratelimit-reset")
        self.__retry_after = int(retry_after) if retry_after else None
        self.__retry_limit_remaining = int(retry_limit_remaining) if retry_limit_remaining else None
        self.__retry_limit_reset = int(retry_limit_reset) if retry_limit_reset else None

    def __wait_for_reset(self) -> None:
        if self.__retry_limit_remaining != 0:
            return
        retry_limit_reset_str: Optional[datetime] = datetime.fromtimestamp(self.__retry_limit_reset) \
            if self.__retry_limit_reset else None
        txt: str = str(f"Status={self.__status_code}, "
                       f"retry_after={self.__retry_after}, "
                       f"retry_limit_remaining={self.__retry_limit_remaining}, "
                       f"retry_limit_reset={self.__retry_limit_reset}, "
                       f"retry_limit_reset={retry_limit_reset_str}")
        log.info(f"Update rate limit: {txt}")
        if self.__retry_limit_reset is None:
            log.warning("Rate limit is exhausted but no reset time was reported. Not waiting")
            return
        sleep_time: int = max(0, self.__retry_limit_reset - int(round(time.time())))
        log.info(f"Waiting for reset: {sleep_time} seconds")
        time.sleep(sleep_time)
        log.info("Done waiting for reset")


class GithubGraphqlRateLimit(GithubRateLimit):

    def is_limited(self, response: Response) -> bool:
        return super().is_limited(response) or (response.status_code == 200 and self.__has_limit_error(response))

    def __has_limit_error(self, response: Response) -> bool:
        try:
            body: Any = response.json()
        except ValueError:
            return False
        if not isinstance(body, dict):
            return False
        return any(self.__is_limit_error(error) for error in body.get("errors") or [])

    @staticmethod
    def __is_limit_error(error: Any) -> bool:
        if not isinstance(error, dict):
            return False
        return error.get("type") == "RATE_LIMITED" or "rate limit" in str(error.get("message", "")).lower()
