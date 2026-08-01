from datetime import datetime
from pathlib import Path
from typing import Optional
import logging
from logging import Logger

from anki_addons_dataset.collector.enricher import Enricher
from anki_addons_dataset.collector.github.handler.repo_info_repo_handler import GithubRepoMeta
from anki_addons_dataset.common.data_types import AddonInfo, LanguageName, GithubInfo, AddonId, \
    AddonInfos, GithubRepo, GitHubLink, AddonManifest, DependencyName
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.common.json_helper import JsonHelper
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


class GithubEnricher(Enricher):
    __name: str = "GitHub"

    def __init__(self, snapshot_dir: SnapshotDir, github_service: GithubService):
        super().__init__(name=self.__name)
        self.__stage_dir: Path = snapshot_dir.get_stage_dir() / "3-enricher" / "github"
        self.__github_service: GithubService = github_service
        self.__github_infos: dict[AddonId, GithubInfo] = {}

    def enrich(self, addon_infos: AddonInfos) -> AddonInfos:
        return AddonInfos([self.__enrich(addon_info, self.__github_infos[addon_info.header.id])
                           for addon_info in addon_infos])

    def _download(self, addon_info: AddonInfo) -> None:
        if addon_info.github and addon_info.github.github_repo:
            github_repo: Optional[GithubRepo] = addon_info.github.github_repo
            github_links: list[GitHubLink] = addon_info.github.github_links
            # get_stars_count runs before get_repo_info (both share info.json), and get_tests_count runs
            # before get_manifest/get_dependencies (both read the repo tree), so each is fetched once.
            language_bytes: dict[LanguageName, int] = self.__github_service.get_languages(github_repo)
            stars: int = self.__github_service.get_stars_count(github_repo)
            last_commit: Optional[datetime] = self.__github_service.get_last_commit(github_repo)
            action_count: Optional[int] = self.__github_service.get_action_count(github_repo)
            tests_count: Optional[int] = self.__github_service.get_tests_count(github_repo)
            repo_meta: GithubRepoMeta = self.__github_service.get_repo_info(github_repo)
            manifest: Optional[AddonManifest] = self.__github_service.get_manifest(github_repo)
            dependencies: list[DependencyName] = self.__github_service.get_dependencies(github_repo)
            readme: Optional[str] = self.__github_service.get_readme(github_repo)
            ai_tooling_markers: list[str] = self.__github_service.get_ai_tooling_markers(github_repo, readme)
        else:
            github_repo: Optional[GithubRepo] = None
            github_links: list[GitHubLink] = []
            language_bytes: dict[LanguageName, int] = {}
            stars: int = 0
            last_commit: Optional[datetime] = None
            action_count: Optional[int] = None
            tests_count: Optional[int] = None
            repo_meta: GithubRepoMeta = GithubRepoMeta()
            manifest: Optional[AddonManifest] = None
            dependencies: list[DependencyName] = []
            readme: Optional[str] = None
            ai_tooling_markers: list[str] = []
        github_info: GithubInfo = GithubInfo(
            github_links, github_repo, list(language_bytes.keys()), stars, last_commit, action_count, tests_count,
            license=repo_meta.license, forks=repo_meta.forks, open_issues=repo_meta.open_issues,
            size_kb=repo_meta.size_kb, topics=repo_meta.topics, repo_description=repo_meta.repo_description,
            homepage=repo_meta.homepage, archived=repo_meta.archived, pushed_at=repo_meta.pushed_at,
            created_at=repo_meta.created_at, primary_language=self.__primary_language(language_bytes),
            language_bytes=language_bytes, manifest=manifest, dependencies=dependencies, readme=readme,
            ai_tooling_markers=ai_tooling_markers)
        self.__github_infos[addon_info.header.id] = github_info

    def _done(self) -> int:
        return len(self.__github_infos)

    @staticmethod
    def __primary_language(language_bytes: dict[LanguageName, int]) -> Optional[LanguageName]:
        if not language_bytes:
            return None
        return max(language_bytes.items(), key=lambda item: item[1])[0]

    def __enrich(self, addon_info: AddonInfo, github_info: GithubInfo) -> AddonInfo:
        enriched_addon_info: AddonInfo = AddonInfo(addon_info.header, addon_info.page, github_info, addon_info.forum)
        addon_json_file: Path = self.__stage_dir / f"{addon_info.header.id}.json"
        JsonHelper.write_addon_info_to_file(addon_info, addon_json_file)
        log.info(f"Enriched ({self.__name}): {addon_info.header.id}")
        return enriched_addon_info
