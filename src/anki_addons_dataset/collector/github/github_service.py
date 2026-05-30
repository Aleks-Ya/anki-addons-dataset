from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import logging
from logging import Logger

from requests import Response

from anki_addons_dataset.collector.github.github_rest_client import GithubRestClient
from anki_addons_dataset.collector.github.handler.actions_repo_handler import ActionsRepoHandler
from anki_addons_dataset.collector.github.handler.languages_repo_handler import LanguagesRepoHandler
from anki_addons_dataset.collector.github.handler.last_commit_repo_handler import LastCommitRepoHandler
from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler
from anki_addons_dataset.collector.github.handler.stars_repo_handler import StarsRepoHandler
from anki_addons_dataset.collector.github.handler.tests_repo_handler import TestsRepoHandler
from anki_addons_dataset.common.data_types import GithubRepo, LanguageName
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


class GithubService:

    def __init__(self, snapshot_dir: SnapshotDir, github_rest_client: GithubRestClient):
        self.__raw_dir: Path = snapshot_dir.get_raw_dir() / "2-github"
        self.__stage_dir: Path = snapshot_dir.get_stage_dir() / "2-github"
        self.__github_rest_client: GithubRestClient = github_rest_client

    def get_languages(self, repo: GithubRepo) -> dict[LanguageName, int]:
        handler: RepoHandler = LanguagesRepoHandler(repo, self.__raw_dir, self.__stage_dir)
        languages: Optional[dict[LanguageName, int]] = self.__get_value(handler)
        if languages is None:
            return {}
        return languages

    def get_stars_count(self, repo: GithubRepo) -> int:
        handler: RepoHandler = StarsRepoHandler(repo, self.__raw_dir, self.__stage_dir)
        stars_count: Optional[int] = self.__get_value(handler)
        if stars_count is None:
            raise ValueError(f"Stars count is None for repo: {repo}")
        return stars_count

    def get_last_commit(self, repo: GithubRepo) -> Optional[datetime]:
        handler: RepoHandler = LastCommitRepoHandler(repo, self.__raw_dir, self.__stage_dir)
        return self.__get_value(handler)

    def get_action_count(self, repo: GithubRepo) -> Optional[int]:
        handler: RepoHandler = ActionsRepoHandler(repo, self.__raw_dir, self.__stage_dir)
        return self.__get_value(handler)

    def get_tests_count(self, repo: GithubRepo) -> Optional[int]:
        handler: RepoHandler = TestsRepoHandler(repo, self.__raw_dir, self.__stage_dir)
        return self.__get_value(handler)

    def __get_value(self, handler: RepoHandler) -> Optional[Any]:
        if not handler.is_downloaded():
            if handler.is_repo_marked_as_not_found():
                return handler.get_not_found_return_value()
            url: str = handler.get_url()
            response: Response = self.__github_rest_client.get_from_url(url)
            if response.status_code == 200:
                handler.status_200(response)
            elif response.status_code == 404:
                handler.status_404()
            elif response.status_code == 409:
                handler.status_409(response)
            else:
                handler.status_other(response)
        return_value: Optional[Any] = handler.extract_return_value()
        handler.write_stage(return_value)
        return return_value
