import copy
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Optional
import logging
from logging import Logger

from anki_addons_dataset.collector.enricher import Enricher
from anki_addons_dataset.collector.github.handler.repo_info_repo_handler import GithubRepoMeta
from anki_addons_dataset.common.data_types import AddonInfo, LanguageName, GithubInfo, AddonId, \
    AddonInfos, GithubRepo, GithubRepoSource, DependencyName, GithubReadme, GithubRelease, \
    GithubContributor, GithubIssueHistory, GithubManifestFile
from anki_addons_dataset.collector.github.github_repo_selector import GithubRepoSelector
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.common.json_helper import JsonHelper
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


class GithubEnricher(Enricher):
    __name: str = "GitHub"
    __online_pool_size: int = 3
    __offline_pool_size: int = 50

    def __init__(self, snapshot_dir: SnapshotDir, github_service: GithubService,
                 github_repo_selector: GithubRepoSelector, offline: bool = False):
        # Offline, the pool waits on AI repo choices rather than on the GitHub rate limit.
        super().__init__(name=self.__name,
                         pool_size=self.__offline_pool_size if offline else self.__online_pool_size)
        self.__github_repo_selector: GithubRepoSelector = github_repo_selector
        self.__stage_dir: Path = snapshot_dir.get_stage_dir() / "3-enricher" / "github"
        self.__github_service: GithubService = github_service
        self.__github_infos: dict[AddonId, Optional[GithubInfo]] = {}
        self.__lock: Lock = Lock()

    def enrich(self, addon_infos: AddonInfos) -> AddonInfos:
        return AddonInfos([self.__enrich(addon_info, self.__github_infos[addon_info.header.id])
                           for addon_info in addon_infos])

    def _download(self, addon_info: AddonInfo) -> None:
        github_info: Optional[GithubInfo] = self.__select(addon_info)
        with self.__lock:
            self.__github_infos[addon_info.header.id] = github_info

    def __select(self, addon_info: AddonInfo) -> Optional[GithubInfo]:
        decided: Optional[tuple[GithubRepo, GithubRepoSource]] = self.__github_repo_selector.decided_repo(addon_info)
        if decided is not None:
            decided_repo, repo_source = decided
            return copy.replace(self.__fetch(decided_repo), repo_source=repo_source)
        # Fetching first lets DOWNLOAD fill the raw cache; a repo without data (404, or never downloaded
        # into an old snapshot) would only show the AI an empty candidate.
        fetched: list[GithubInfo] = [self.__fetch(repo) for repo in
                                     self.__github_repo_selector.candidate_repos(addon_info.page.github_links)]
        candidates: list[GithubInfo] = [candidate for candidate in fetched
                                        if self.__github_service.has_repo_data(candidate.github_repo)]
        return self.__github_repo_selector.select(addon_info, candidates)

    def __fetch(self, github_repo: GithubRepo) -> GithubInfo:
        # get_stars_count runs before get_repo_info (both share info.json), and get_tests_count runs
        # before get_manifest_files/get_dependencies (both read the repo tree), so each is fetched once.
        language_bytes: dict[LanguageName, int] = self.__github_service.get_languages(github_repo)
        stars: int = self.__github_service.get_stars_count(github_repo)
        last_commit: Optional[datetime] = self.__github_service.get_last_commit(github_repo)
        action_count: Optional[int] = self.__github_service.get_action_count(github_repo)
        tests_count: Optional[int] = self.__github_service.get_tests_count(github_repo)
        repo_meta: GithubRepoMeta = self.__github_service.get_repo_info(github_repo)
        manifest_files: list[GithubManifestFile] = self.__github_service.get_manifest_files(github_repo)
        first_manifest: Optional[GithubManifestFile] = manifest_files[0] if manifest_files else None
        dependencies: list[DependencyName] = self.__github_service.get_dependencies(github_repo)
        readme: Optional[GithubReadme] = self.__github_service.get_readme(github_repo)
        ai_tooling_markers: list[str] = self.__github_service.get_ai_tooling_markers(github_repo, readme)
        releases: Optional[list[GithubRelease]] = self.__github_service.get_releases(github_repo)
        contributors: Optional[list[GithubContributor]] = self.__github_service.get_contributors(github_repo)
        weekly_commits: Optional[list[int]] = self.__github_service.get_weekly_commits(github_repo)
        issue_history: Optional[GithubIssueHistory] = self.__github_service.get_issue_history(github_repo)
        return GithubInfo(
            github_repo, stars, last_commit, action_count, tests_count,
            license=repo_meta.license, fork_count=repo_meta.fork_count, open_issues=repo_meta.open_issues,
            size_kb=repo_meta.size_kb, topics=repo_meta.topics, repo_description=repo_meta.repo_description,
            homepage=repo_meta.homepage, archived=repo_meta.archived, pushed_at=repo_meta.pushed_at,
            created_at=repo_meta.created_at, primary_language=self.__primary_language(language_bytes),
            language_bytes=language_bytes, manifest=first_manifest.manifest if first_manifest else None,
            manifest_path=first_manifest.path if first_manifest else None,
            manifest_files=manifest_files if len(manifest_files) > 1 else [],
            dependencies=dependencies, readme=readme,
            ai_tooling_markers=ai_tooling_markers, fork_source=repo_meta.fork_source,
            canonical_repo=repo_meta.canonical_repo, releases=releases,
            contributors=contributors, weekly_commits=weekly_commits, issue_history=issue_history)

    def _done(self) -> int:
        with self.__lock:
            return len(self.__github_infos)

    @staticmethod
    def __primary_language(language_bytes: dict[LanguageName, int]) -> Optional[LanguageName]:
        if not language_bytes:
            return None
        return max(language_bytes.items(), key=lambda item: item[1])[0]

    def __enrich(self, addon_info: AddonInfo, github_info: Optional[GithubInfo]) -> AddonInfo:
        enriched_addon_info: AddonInfo = copy.replace(addon_info, github=github_info)
        addon_json_file: Path = self.__stage_dir / f"{addon_info.header.id}.json"
        JsonHelper.write_addon_info_to_file(addon_info, addon_json_file)
        log.info(f"Enriched ({self.__name}): {addon_info.header.id}")
        return enriched_addon_info
