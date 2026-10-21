import logging
import re
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.collector.github.handler.tag_names_repo_handler import TagNamesRepoHandler
from anki_addons_dataset.common.anki_version import AnkiVersionCodec
from anki_addons_dataset.common.data_types import AnkiRelease, AnkiVersion, GithubRepo, GithubRepoName, \
    GithubUserName
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


class AnkiVersionsCollector:
    anki_repo: GithubRepo = GithubRepo(GithubUserName("ankitects"), GithubRepoName("anki"))
    __stable_re: re.Pattern[str] = re.compile(r"(\d+)\.(\d+)(?:\.\d+)?")

    def __init__(self, github_service: GithubService) -> None:
        self.__github_service: GithubService = github_service

    def download(self) -> None:
        tag_names: list[str] = self.__github_service.get_tag_names(AnkiVersionsCollector.anki_repo)
        log.info(f"Anki repo has {len(tag_names)} tags, {len(self.to_releases(tag_names))} stable releases")

    @staticmethod
    def read(snapshot_dir: SnapshotDir) -> Optional[list[AnkiRelease]]:
        handler: TagNamesRepoHandler = TagNamesRepoHandler(AnkiVersionsCollector.anki_repo,
                                                           snapshot_dir.get_raw_dir() / "2-github",
                                                           snapshot_dir.get_stage_dir() / "2-github")
        if not handler.is_downloaded():
            return None
        return AnkiVersionsCollector.to_releases(handler.extract_return_value())

    @staticmethod
    def to_releases(tag_names: list[str]) -> list[AnkiRelease]:
        releases: set[AnkiRelease] = set()
        for tag_name in tag_names:
            match: Optional[re.Match[str]] = AnkiVersionsCollector.__stable_re.fullmatch(tag_name)
            if not match:
                continue
            major: int = int(match.group(1))
            minor: int = int(match.group(2))
            if major < 2 or (major == 2 and minor != 1):
                continue
            releases.add(AnkiRelease(AnkiVersion(tag_name), AnkiVersionCodec.to_point(tag_name)))
        return sorted(releases, key=lambda release: release.point_version, reverse=True)
