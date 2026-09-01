from pathlib import Path
from typing import Optional
import logging
from logging import Logger

from requests import Response
import requests

from anki_addons_dataset.collector.github.github_rate_limit import GithubRateLimit

log: Logger = logging.getLogger(__name__)


class GithubRestClient:

    def __init__(self, offline: bool):
        token: str = self.read_token()
        self.__headers: dict[str, str] = {
            'Authorization': f'Bearer {token}'
        }
        self.__offline: bool = offline
        self.__rate_limit: GithubRateLimit = GithubRateLimit()

    @staticmethod
    def get_token_file() -> Path:
        return Path.home() / ".github" / "token.txt"

    @staticmethod
    def read_token() -> str:
        token_file: Path = GithubRestClient.get_token_file()
        if not token_file.is_file():
            raise FileNotFoundError(f"Missing GitHub token file {token_file}. "
                                    f"Create it with a GitHub personal access token.")
        token: str = token_file.read_text().strip()
        if not token:
            raise ValueError(f"Empty GitHub token file {token_file}")
        return token

    def verify_token(self) -> Optional[int]:
        """Verify the token against the GitHub API and return the remaining request quota.

        Called by the `info` step as a preflight check. Queries `/rate_limit`, which GitHub
        does not count against the quota it reports."""
        url: str = "https://api.github.com/rate_limit"
        response: Response = self.get_from_url(url)
        if response.status_code in (401, 403):
            raise PermissionError(f"GitHub rejected the token (HTTP {response.status_code}) at {url}. "
                                  f"Check the token in {self.get_token_file()}")
        response.raise_for_status()
        return self.__rate_limit.get_limit_remaining()

    def get_from_url(self, url: str, etag: Optional[str] = None) -> Response:
        log.debug(f"Downloading {url} (limit {self.__rate_limit.get_limit_remaining()})")
        if self.__offline:
            raise RuntimeError("Offline mode is enabled")
        self.__rate_limit.wait_for_reset()
        headers: dict[str, str] = dict(self.__headers)
        if etag:
            headers["If-None-Match"] = etag
        response: Response = requests.request("GET", url, headers=headers)
        self.__rate_limit.update_rate_limit(response)
        return response
