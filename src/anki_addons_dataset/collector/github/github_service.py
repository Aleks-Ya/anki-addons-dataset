from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Any, Optional

from requests import Response
import requests

from anki_addons_dataset.collector.github.handler.actions_repo_handler import ActionsRepoHandler
from anki_addons_dataset.collector.github.handler.languages_repo_handler import LanguagesRepoHandler
from anki_addons_dataset.collector.github.handler.last_commit_repo_handler import LastCommitRepoHandler
from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler
from anki_addons_dataset.collector.github.handler.stars_repo_handler import StarsRepoHandler
from anki_addons_dataset.collector.github.handler.tests_repo_handler import TestsRepoHandler
from anki_addons_dataset.common.data_types import GitHubRepo, LanguageName
from anki_addons_dataset.common.working_dir import VersionDir


class GithubService:

    def __init__(self, version_dir: VersionDir, sleep_sec: int, offline: bool):
        token_file: Path = Path.home() / ".github" / "token.txt"
        token: str = token_file.read_text().strip()
        self.__headers: dict[str, str] = {
            'Authorization': f'Bearer {token}'
        }
        self.__raw_dir: Path = version_dir.get_raw_dir() / "2-github"
        self.__stage_dir: Path = version_dir.get_stage_dir() / "2-github"
        self.__sleep_sec: int = sleep_sec
        self.__offline: bool = offline

    def get_languages(self, repo: GitHubRepo) -> dict[LanguageName, int]:
        handler: RepoHandler = LanguagesRepoHandler(repo, self.__raw_dir, self.__stage_dir)
        return self.__get_value(handler, repo)

    def get_stars_count(self, repo: GitHubRepo) -> int:
        handler: RepoHandler = StarsRepoHandler(repo, self.__raw_dir, self.__stage_dir)
        return self.__get_value(handler, repo)

    def get_last_commit(self, repo: GitHubRepo) -> Optional[datetime]:
        handler: RepoHandler = LastCommitRepoHandler(repo, self.__raw_dir, self.__stage_dir)
        return self.__get_value(handler, repo)

    def get_action_count(self, repo: GitHubRepo) -> Optional[int]:
        handler: RepoHandler = ActionsRepoHandler(repo, self.__raw_dir, self.__stage_dir)
        return self.__get_value(handler, repo)

    def get_tests_count(self, repo: GitHubRepo) -> Optional[int]:
        handler: RepoHandler = TestsRepoHandler(repo, self.__raw_dir, self.__stage_dir)
        return self.__get_value(handler, repo)

    def __get_value(self, handler: RepoHandler, repo: GitHubRepo) -> Optional[Any]:
        if not repo:
            return None
        if not handler.is_downloaded():
            if handler.is_repo_marked_as_not_found():
                return handler.get_not_found_return_value()
            url: str = handler.get_url()
            print(f"Downloading {url} for {repo.get_id()}")
            if self.__offline:
                raise RuntimeError("Offline mode is enabled")
            sleep(self.__sleep_sec)
            response: Response = requests.request("GET", url, headers=self.__headers)
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
