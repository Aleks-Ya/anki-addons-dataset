import logging
import re
from datetime import date
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.collector.github.handler.releases_repo_handler import ReleasesRepoHandler
from anki_addons_dataset.collector.github.handler.tag_names_repo_handler import TagNamesRepoHandler
from anki_addons_dataset.common.anki_version import AnkiVersionCodec
from anki_addons_dataset.common.data_types import AnkiRelease, AnkiVersion, GithubRelease, GithubRepo, \
    GithubRepoName, GithubUserName
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


class AnkiVersionsCollector:
    anki_repo: GithubRepo = GithubRepo(GithubUserName("ankitects"), GithubRepoName("anki"))
    __stable_re: re.Pattern[str] = re.compile(r"(\d+)\.(\d+)(?:\.\d+)?")

    def __init__(self, github_service: GithubService) -> None:
        self.__github_service: GithubService = github_service

    def download(self) -> None:
        tag_names: list[str] = self.__github_service.get_tag_names(AnkiVersionsCollector.anki_repo)
        github_releases: list[GithubRelease] = self.__github_service.get_releases(AnkiVersionsCollector.anki_repo) or []
        log.info(f"Anki repo has {len(tag_names)} tags, {len(self.to_releases(tag_names, github_releases))} "
                 f"stable releases, {len(github_releases)} GitHub releases")

    @staticmethod
    def read(snapshot_dir: SnapshotDir) -> Optional[list[AnkiRelease]]:
        handler: TagNamesRepoHandler = TagNamesRepoHandler(AnkiVersionsCollector.anki_repo,
                                                           snapshot_dir.get_raw_dir() / "2-github",
                                                           snapshot_dir.get_stage_dir() / "2-github")
        if not handler.is_downloaded():
            return None
        return AnkiVersionsCollector.to_releases(handler.extract_return_value(),
                                                 AnkiVersionsCollector.__read_github_releases(snapshot_dir))

    @staticmethod
    def __read_github_releases(snapshot_dir: SnapshotDir) -> list[GithubRelease]:
        handler: ReleasesRepoHandler = ReleasesRepoHandler(AnkiVersionsCollector.anki_repo,
                                                           snapshot_dir.get_raw_dir() / "2-github",
                                                           snapshot_dir.get_stage_dir() / "2-github")
        if not handler.is_downloaded():
            log.warning(f"No Anki releases in {snapshot_dir.get_raw_dir()}, the anki_versions table has no release "
                        f"dates. Run the 'download -d {snapshot_dir.snapshot_dir_to_snapshot_date()}' operation "
                        f"to fetch them.")
            return []
        return handler.extract_return_value() or []

    @staticmethod
    def to_releases(tag_names: list[str], github_releases: list[GithubRelease]) -> list[AnkiRelease]:
        release_dates: dict[str, date] = {release.tag_name: release.published_at.date()
                                          for release in github_releases if release.published_at}
        releases: set[AnkiRelease] = set()
        for tag_name in tag_names:
            match: Optional[re.Match[str]] = AnkiVersionsCollector.__stable_re.fullmatch(tag_name)
            if not match:
                continue
            major: int = int(match.group(1))
            minor: int = int(match.group(2))
            if major < 2 or (major == 2 and minor != 1):
                continue
            releases.add(AnkiRelease(AnkiVersion(tag_name), AnkiVersionCodec.to_point(tag_name),
                                     release_dates.get(tag_name)))
        return sorted(releases, key=lambda release: release.point_version, reverse=True)
