import re
from pathlib import Path
from typing import Any, Optional
import logging
from logging import Logger

from requests import Response
import requests

from anki_addons_dataset.collector.github.github_rate_limit import GithubRateLimit

log: Logger = logging.getLogger(__name__)


class GithubRestClient:
    graphql_url: str = "https://api.github.com/graphql"
    __actions_url: re.Pattern[str] = re.compile(r"/repos/[^/]+/[^/]+/actions/")
    __limited_retries: int = 3

    def __init__(self, offline: bool, token_file: Path):
        self.__token_file: Path = token_file
        token: str = self.read_token()
        self.__headers: dict[str, str] = {
            'Authorization': f'Bearer {token}'
        }
        self.__offline: bool = offline
        self.__rate_limit: GithubRateLimit = GithubRateLimit()
        self.__graphql_rate_limit: GithubRateLimit = GithubRateLimit()
        self.__actions_rate_limit: GithubRateLimit = GithubRateLimit()

    def get_token_file(self) -> Path:
        return self.__token_file

    def read_token(self) -> str:
        token_file: Path = self.__token_file
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
        rate_limit: GithubRateLimit = self.__actions_rate_limit if self.__actions_url.search(url) \
            else self.__rate_limit
        log.debug(f"Downloading {url} (limit {rate_limit.get_limit_remaining()})")
        if self.__offline:
            raise RuntimeError("Offline mode is enabled")
        headers: dict[str, str] = dict(self.__headers)
        if etag:
            headers["If-None-Match"] = etag
        return self.__send(rate_limit, "GET", url, headers=headers)

    def post_graphql(self, query: str, variables: dict[str, str]) -> Response:
        log.debug(f"Querying GraphQL {variables} (limit {self.__graphql_rate_limit.get_limit_remaining()})")
        if self.__offline:
            raise RuntimeError("Offline mode is enabled")
        return self.__send(self.__graphql_rate_limit, "POST", self.graphql_url, headers=self.__headers,
                           json={"query": query, "variables": variables})

    def __send(self, rate_limit: GithubRateLimit, method: str, url: str, **kwargs: Any) -> Response:
        rate_limit.wait_for_reset()
        response: Response = requests.request(method, url, **kwargs)
        rate_limit.update_rate_limit(response)
        for _ in range(self.__limited_retries):
            if not rate_limit.is_limited(response):
                break
            rate_limit.wait_after_limited(response)
            response = requests.request(method, url, **kwargs)
            rate_limit.update_rate_limit(response)
        return response
