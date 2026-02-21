from pathlib import Path
import logging
from logging import Logger

from requests import Response
import requests

from anki_addons_dataset.collector.github.github_rate_limit import GithubRateLimit

log: Logger = logging.getLogger(__name__)


class GithubRestClient:

    def __init__(self, offline: bool):
        token_file: Path = Path.home() / ".github" / "token.txt"
        token: str = token_file.read_text().strip()
        self.__headers: dict[str, str] = {
            'Authorization': f'Bearer {token}'
        }
        self.__offline: bool = offline
        self.__rate_limit: GithubRateLimit = GithubRateLimit()

    def get_from_url(self, url: str) -> Response:
        log.debug(f"Downloading {url} (limit {self.__rate_limit.get_limit_remaining()})")
        if self.__offline:
            raise RuntimeError("Offline mode is enabled")
        self.__rate_limit.wait_for_reset()
        response: Response = requests.request("GET", url, headers=self.__headers)
        self.__rate_limit.update_rate_limit(response)
        return response
