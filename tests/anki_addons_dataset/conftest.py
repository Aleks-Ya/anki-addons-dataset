import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import Mock

from pydiscourse import DiscourseClient
from pytest import fixture

from anki_addons_dataset.collector.ankiforum.ankiforum_enricher import AnkiForumEnricher
from anki_addons_dataset.collector.ankiforum.ankiforum_service import TopicSlug, TopicId, AnkiForumService
from anki_addons_dataset.collector.ankiweb.addon_page_downloader import AddonPageDownloader
from anki_addons_dataset.collector.ankiweb.addon_page_parser import AddonPageParser
from anki_addons_dataset.collector.ankiweb.addons_page_downloader import AddonsPageDownloader
from anki_addons_dataset.collector.ankiweb.ankiweb_service import AnkiWebService
from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.collector.github.github_enricher import GithubEnricher
from anki_addons_dataset.collector.github.github_rest_client import GithubRestClient
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonId, GitHubRepo, GithubUserName, GithubRepoName, LastPostedAt, URL
from anki_addons_dataset.common.working_dir import WorkingDir, VersionDir


@fixture
def working_dir_path() -> Path:
    return Path(tempfile.mkdtemp())


@fixture
def working_dir(working_dir_path: Path) -> WorkingDir:
    return WorkingDir(working_dir_path)


@fixture
def version_dir(working_dir: WorkingDir) -> VersionDir:
    return working_dir.get_version_dir(date.fromisoformat("2025-01-25")).create()


@fixture
def overrider(version_dir: VersionDir) -> Overrider:
    return Overrider(version_dir)


@fixture
def note_size_addon_id() -> AddonId:
    return AddonId(1188705668)


@fixture
def hyper_tts_addon_id() -> AddonId:
    return AddonId(111623432)


@fixture
def page_downloader() -> PageDownloader:
    return Mock()


@fixture
def addon_page_parser(overrider: Overrider) -> AddonPageParser:
    return AddonPageParser(overrider)


@fixture
def offline() -> bool:
    return False


@fixture
def addons_page_downloader(page_downloader: PageDownloader, version_dir: VersionDir,
                           offline: bool) -> AddonsPageDownloader:
    return AddonsPageDownloader(page_downloader, version_dir, offline)


@fixture
def addon_page_downloader(page_downloader: PageDownloader, version_dir: VersionDir,
                          addon_page_parser: AddonPageParser, offline: bool) -> AddonPageDownloader:
    return AddonPageDownloader(page_downloader, version_dir, addon_page_parser, offline)


@fixture
def ankiweb_service(addons_page_downloader: AddonsPageDownloader,
                    addon_page_downloader: AddonPageDownloader) -> AnkiWebService:
    return AnkiWebService(addons_page_downloader, addon_page_downloader)


@fixture
def github_rest_client() -> GithubRestClient:
    return Mock()


@fixture
def topic_slug() -> TopicSlug:
    return TopicSlug("note-size-addon-support")


@fixture
def topic_id() -> TopicId:
    return TopicId(46001)


@fixture
def anki_forum_url(topic_slug: TopicSlug, topic_id: TopicId) -> URL:
    return URL(f"https://forums.ankiweb.net/t/{topic_slug}/{topic_id}")


@fixture
def last_posted_at() -> LastPostedAt:
    return LastPostedAt(datetime(2023, 9, 10, 12, 0, 0, 0, tzinfo=timezone.utc))


@fixture
def discourse_client() -> DiscourseClient:
    return DiscourseClient(host="", api_username=None, api_key=None)


@fixture
def anki_forum_service(discourse_client: DiscourseClient, version_dir: VersionDir, offline: bool) -> AnkiForumService:
    return AnkiForumService(discourse_client, version_dir, offline)


@fixture
def github_service(version_dir: VersionDir, github_rest_client: GithubRestClient) -> GithubService:
    return GithubService(version_dir, github_rest_client)


@fixture
def github_enricher(version_dir: VersionDir, github_service: GithubService) -> GithubEnricher:
    return GithubEnricher(version_dir, github_service)


@fixture
def anki_forum_enricher(version_dir: VersionDir, anki_forum_service: AnkiForumService) -> AnkiForumEnricher:
    return AnkiForumEnricher(version_dir, anki_forum_service)


@fixture
def github_repo() -> GitHubRepo:
    return GitHubRepo(GithubUserName("John"), GithubRepoName("app"))
