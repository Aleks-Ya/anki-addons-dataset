import datetime
import time
from typing import Optional
import logging
from logging import Logger

from requests import Response
from requests.structures import CaseInsensitiveDict

log: Logger = logging.getLogger(__name__)


class GithubRateLimit:

    def __init__(self):
        self.__status_code: Optional[int] = None
        self.__retry_after: Optional[int] = None
        self.__retry_limit_remaining: Optional[int] = None
        self.__retry_limit_reset: Optional[int] = None

    def update_rate_limit(self, response: Response) -> None:
        self.__status_code = response.status_code
        headers: CaseInsensitiveDict[str] = response.headers
        retry_after: Optional[str] = headers.get("retry-after")
        retry_limit_remaining: Optional[str] = headers.get("x-ratelimit-remaining")
        retry_limit_reset: Optional[str] = headers.get("x-ratelimit-reset")
        self.__retry_after = int(retry_after) if retry_after else None
        self.__retry_limit_remaining = int(retry_limit_remaining) if retry_limit_remaining else None
        self.__retry_limit_reset = int(retry_limit_reset) if retry_limit_reset else None

    def wait_for_reset(self) -> None:
        if self.__retry_limit_remaining and self.__retry_limit_remaining == 0:
            txt: str = str(f"Status={self.__status_code}, "
                           f"retry_after={self.__retry_after}, "
                           f"retry_limit_remaining={self.__retry_limit_remaining}, "
                           f"retry_limit_reset={self.__retry_limit_reset}, "
                           f"retry_limit_reset={datetime.datetime.fromtimestamp(self.__retry_limit_reset)}")
            log.info(f"Update rate limit: {txt}")
            sleep_time: int = self.__retry_limit_reset - int(round(time.time()))
            log.info(f"Waiting for reset: {sleep_time} seconds")
            time.sleep(sleep_time)
            log.info("Done waiting for reset")

    def get_limit_remaining(self) -> Optional[int]:
        return self.__retry_limit_remaining
