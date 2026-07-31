from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import logging
from logging import Logger

from requests import Response

from anki_addons_dataset.collector.github.github_rest_client import GithubRestClient
from anki_addons_dataset.collector.github.handler.actions_repo_handler import ActionsRepoHandler
from anki_addons_dataset.collector.github.handler.contents_repo_handler import ContentsRepoHandler
from anki_addons_dataset.collector.github.handler.dependencies_parser import DependenciesParser
from anki_addons_dataset.collector.github.handler.languages_repo_handler import LanguagesRepoHandler
from anki_addons_dataset.collector.github.handler.last_commit_repo_handler import LastCommitRepoHandler
from anki_addons_dataset.collector.github.handler.manifest_parser import ManifestParser
from anki_addons_dataset.collector.github.handler.readme_repo_handler import ReadmeRepoHandler
from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler
from anki_addons_dataset.collector.github.handler.repo_info_repo_handler import GithubRepoMeta, RepoInfoRepoHandler
from anki_addons_dataset.collector.github.handler.stars_repo_handler import StarsRepoHandler
from anki_addons_dataset.collector.github.handler.tests_repo_handler import TestsRepoHandler
from anki_addons_dataset.collector.github.handler.tree_entries_repo_handler import TreeEntriesRepoHandler
from anki_addons_dataset.common.data_types import AddonManifest, DependencyName, GithubRepo, LanguageName
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


class GithubService:

    def __init__(self, snapshot_dir: SnapshotDir, github_rest_client: GithubRestClient,
                 prev_snapshot_dir: Optional[SnapshotDir] = None, offline: bool = False):
        self.__raw_dir: Path = snapshot_dir.get_raw_dir() / "2-github"
        self.__stage_dir: Path = snapshot_dir.get_stage_dir() / "2-github"
        self.__prev_raw_dir: Optional[Path] = \
            prev_snapshot_dir.get_raw_dir() / "2-github" if prev_snapshot_dir else None
        self.__github_rest_client: GithubRestClient = github_rest_client
        self.__offline: bool = offline

    def get_languages(self, repo: GithubRepo) -> dict[LanguageName, int]:
        handler: RepoHandler = LanguagesRepoHandler(repo, self.__raw_dir, self.__stage_dir, self.__prev_raw_dir)
        languages: Optional[dict[LanguageName, int]] = self.__get_value(handler)
        if languages is None:
            return {}
        return languages

    def get_stars_count(self, repo: GithubRepo) -> int:
        handler: RepoHandler = StarsRepoHandler(repo, self.__raw_dir, self.__stage_dir, self.__prev_raw_dir)
        stars_count: Optional[int] = self.__get_value(handler)
        if stars_count is None:
            raise ValueError(f"Stars count is None for repo: {repo}")
        return stars_count

    def get_last_commit(self, repo: GithubRepo) -> Optional[datetime]:
        handler: RepoHandler = LastCommitRepoHandler(repo, self.__raw_dir, self.__stage_dir, self.__prev_raw_dir)
        return self.__get_value(handler)

    def get_action_count(self, repo: GithubRepo) -> Optional[int]:
        handler: RepoHandler = ActionsRepoHandler(repo, self.__raw_dir, self.__stage_dir, self.__prev_raw_dir)
        return self.__get_value(handler)

    def get_tests_count(self, repo: GithubRepo) -> Optional[int]:
        handler: RepoHandler = TestsRepoHandler(repo, self.__raw_dir, self.__stage_dir, self.__prev_raw_dir)
        return self.__get_value(handler)

    def get_repo_info(self, repo: GithubRepo) -> GithubRepoMeta:
        # Shares the cached `info.json` with StarsRepoHandler, so no extra API call is made.
        handler: RepoHandler = RepoInfoRepoHandler(repo, self.__raw_dir, self.__stage_dir, self.__prev_raw_dir)
        meta: Optional[GithubRepoMeta] = self.__get_value(handler)
        return meta if meta is not None else GithubRepoMeta()

    def get_readme(self, repo: GithubRepo) -> Optional[str]:
        handler: RepoHandler = ReadmeRepoHandler(repo, self.__raw_dir, self.__stage_dir, self.__prev_raw_dir)
        return self.__get_value(handler)

    def get_manifest(self, repo: GithubRepo) -> Optional[AddonManifest]:
        path: Optional[str] = self.__find_file(repo, "manifest.json")
        if path is None:
            return None
        return ManifestParser.parse(self.__get_contents(repo, path, "manifest"))

    def get_dependencies(self, repo: GithubRepo) -> list[DependencyName]:
        dependencies: list[DependencyName] = []
        requirements_path: Optional[str] = self.__find_file(repo, "requirements.txt")
        if requirements_path is not None:
            requirements_content: Optional[str] = self.__get_contents(repo, requirements_path, "requirements")
            dependencies.extend(DependenciesParser.parse_requirements(requirements_content))
        pyproject_path: Optional[str] = self.__find_file(repo, "pyproject.toml")
        if pyproject_path is not None:
            pyproject_content: Optional[str] = self.__get_contents(repo, pyproject_path, "pyproject")
            dependencies.extend(DependenciesParser.parse_pyproject(pyproject_content))
        return list(dict.fromkeys(dependencies))

    def __find_file(self, repo: GithubRepo, basename: str) -> Optional[str]:
        # Locates the shallowest file with the given basename in the cached repo tree (root-most wins).
        handler: RepoHandler = TreeEntriesRepoHandler(repo, self.__raw_dir, self.__stage_dir, self.__prev_raw_dir)
        paths: list[str] = self.__get_value(handler) or []
        candidates: list[str] = [path for path in paths if path.rsplit("/", 1)[-1] == basename]
        if not candidates:
            return None
        return min(candidates, key=lambda path: (path.count("/"), path))

    def __get_contents(self, repo: GithubRepo, path: str, raw_name: str) -> Optional[str]:
        handler: RepoHandler = ContentsRepoHandler(
            repo, path, raw_name, self.__raw_dir, self.__stage_dir, self.__prev_raw_dir)
        return self.__get_value(handler)

    def __get_value(self, handler: RepoHandler) -> Optional[Any]:
        if not handler.is_downloaded():
            if handler.is_repo_marked_as_not_found():
                return handler.get_not_found_return_value()
            if self.__offline:
                log.debug(f"Offline mode is enabled. Skip fetching {handler.get_url()}")
                return handler.get_not_found_return_value()
            url: str = handler.get_url()
            etag: Optional[str] = handler.get_prev_etag()
            response: Response = self.__github_rest_client.get_from_url(url, etag)
            if response.status_code == 200:
                handler.status_200(response)
            elif response.status_code == 304:
                handler.status_304()
            elif response.status_code == 404:
                handler.status_404()
            elif response.status_code == 409:
                handler.status_409(response)
            else:
                handler.status_other(response)
        return_value: Optional[Any] = handler.extract_return_value()
        handler.write_stage(return_value)
        return return_value
