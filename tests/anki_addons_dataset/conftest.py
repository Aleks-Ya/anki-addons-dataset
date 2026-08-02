import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydiscourse import DiscourseClient

from anki_addons_dataset.collector.aggregator import Aggregator
from anki_addons_dataset.collector.ankiforum.ankiforum_enricher import AnkiForumEnricher
from anki_addons_dataset.collector.ankiforum.ankiforum_service import TopicSlug, TopicId, AnkiForumService
from anki_addons_dataset.collector.ankiweb.addon_page_downloader import AddonPageDownloader
from anki_addons_dataset.collector.ankiweb.addon_page_parser import AddonPageParser
from anki_addons_dataset.collector.ankiweb.addons_page_downloader import AddonsPageDownloader
from anki_addons_dataset.collector.ankiweb.ankiweb_service import AnkiWebService
from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.collector.dataset_metadata import DatasetMetadata
from anki_addons_dataset.collector.github.github_enricher import GithubEnricher
from anki_addons_dataset.collector.github.github_rest_client import GithubRestClient
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonId, GithubRepo, GithubUserName, GithubRepoName, LastPostedAt, \
    URL, PostsCount, AddonInfo, AddonHeader, AddonPage, GithubInfo, AnkiForumInfo, LanguageName, AddonInfos, \
    DatasetSnapshotMetadata, RawMetadata, AnkiVersion, AddonBranch, HtmlStr, SnapshotDate, ReportDate, ScriptVersion, \
    AddonRating, UpdateDate, AddonTitle, PlainStr
from anki_addons_dataset.common.working_dir import WorkingDir, SnapshotDir
from anki_addons_dataset.exporter.json.json_exporter import JsonExporter
from anki_addons_dataset.exporter.xlsx.xlsx_exporter import XlsxExporter
from anki_addons_dataset.facade.facade import Facade
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient
from anki_addons_dataset.initializer.working_dir_backup import WorkingDirBackup
from anki_addons_dataset.initializer.working_dir_initializer import WorkingDirInitializer


@pytest.fixture
def working_dir_path() -> Path:
    return Path(tempfile.mkdtemp())


@pytest.fixture
def working_dir(working_dir_path: Path) -> WorkingDir:
    return WorkingDir(working_dir_path)


@pytest.fixture
def snapshot_date() -> SnapshotDate:
    return SnapshotDate(date.fromisoformat("2025-01-25"))


@pytest.fixture
def snapshot_dir(working_dir: WorkingDir, snapshot_date: SnapshotDate) -> SnapshotDir:
    return working_dir.get_snapshot_dir(snapshot_date).create()


@pytest.fixture
def overrider(snapshot_dir: SnapshotDir) -> Overrider:
    return Overrider(snapshot_dir)


@pytest.fixture
def note_size_addon_id() -> AddonId:
    return AddonId(1188705668)


@pytest.fixture
def hyper_tts_addon_id() -> AddonId:
    return AddonId(111623432)


@pytest.fixture
def page_downloader() -> PageDownloader:
    return Mock()


@pytest.fixture
def addon_page_parser(overrider: Overrider) -> AddonPageParser:
    return AddonPageParser(overrider)


@pytest.fixture
def offline() -> bool:
    return False


@pytest.fixture
def addons_page_downloader(page_downloader: PageDownloader, snapshot_dir: SnapshotDir,
                           offline: bool) -> AddonsPageDownloader:
    return AddonsPageDownloader(page_downloader, snapshot_dir, offline)


@pytest.fixture
def addon_page_downloader(page_downloader: PageDownloader, snapshot_dir: SnapshotDir,
                          addon_page_parser: AddonPageParser, offline: bool) -> AddonPageDownloader:
    return AddonPageDownloader(page_downloader, snapshot_dir, addon_page_parser, offline)


@pytest.fixture
def ankiweb_service(addons_page_downloader: AddonsPageDownloader,
                    addon_page_downloader: AddonPageDownloader) -> AnkiWebService:
    return AnkiWebService(addons_page_downloader, addon_page_downloader)


@pytest.fixture
def github_rest_client() -> GithubRestClient:
    return Mock()


@pytest.fixture
def topic_slug() -> TopicSlug:
    return TopicSlug("note-size-addon-support")


@pytest.fixture
def topic_id() -> TopicId:
    return TopicId(46001)


@pytest.fixture
def anki_forum_url(topic_slug: TopicSlug, topic_id: TopicId) -> URL:
    return URL(f"https://forums.ankiweb.net/t/{topic_slug}/{topic_id}")


@pytest.fixture
def last_posted_at() -> LastPostedAt:
    return LastPostedAt(datetime(2023, 9, 10, 12, 0, 0, 0, tzinfo=timezone.utc))


@pytest.fixture
def posts_count() -> PostsCount:
    return PostsCount(42)


@pytest.fixture
def addon_header(note_size_addon_id: AddonId) -> AddonHeader:
    return AddonHeader(
        id=note_size_addon_id,
        title=AddonTitle("NoteSize"),
        addon_page_url=URL("https://ankiweb.net/shared/info/1188705668"),
        rating=AddonRating(4),
        update_date=UpdateDate("2023-03-15"),
        anki_version=AnkiVersion("25.09.2~")
    )


@pytest.fixture
def addon_info(addon_header: AddonHeader, github_repo: GithubRepo, topic_slug: TopicSlug, topic_id: TopicId,
               last_posted_at: LastPostedAt, posts_count: PostsCount) -> AddonInfo:
    return AddonInfo(
        header=addon_header,
        page=AddonPage(
            content=HtmlStr("<html><body><h1>Sample addon page content</h1></body></html>"),
            like_number=0,
            dislike_number=0,
            branches=[AddonBranch(min_anki_version=AnkiVersion("24.04.1"),
                                  max_anki_version=AnkiVersion("25.09.2~"),
                                  updated=date(2023, 3, 15))],
            other_links=[],
            description=PlainStr("Sample addon description for full text search"),
            ai_declaration_markers=["chatgpt"]
        ),
        github=GithubInfo(
            github_links=[],
            github_repo=github_repo,
            languages=[LanguageName("Python"), LanguageName("Rust")],
            stars=3,
            last_commit=datetime(2023, 3, 15, 12, 0, 0, 0),
            action_count=5,
            tests_count=7,
            ai_tooling_markers=["claude-code", "cursor"]
        ),
        forum=AnkiForumInfo(
            anki_forum_url=URL("https://forums.ankiweb.net/t/note-size-addon-support/46001"),
            topic_slug=topic_slug,
            topic_id=topic_id,
            last_posted_at=last_posted_at,
            posts_count=posts_count
        )
    )


@pytest.fixture
def addon_infos(addon_info: AddonInfo) -> AddonInfos:
    return AddonInfos([addon_info])


@pytest.fixture
def discourse_client() -> DiscourseClient:
    return DiscourseClient(host="", api_username=None, api_key=None)


@pytest.fixture
def anki_forum_service(discourse_client: DiscourseClient, snapshot_dir: SnapshotDir, offline: bool) -> AnkiForumService:
    return AnkiForumService(discourse_client, snapshot_dir, offline)


@pytest.fixture
def github_service(snapshot_dir: SnapshotDir, github_rest_client: GithubRestClient,
                   offline: bool) -> GithubService:
    return GithubService(snapshot_dir, github_rest_client, offline=offline)


@pytest.fixture
def github_enricher(snapshot_dir: SnapshotDir, github_service: GithubService) -> GithubEnricher:
    return GithubEnricher(snapshot_dir, github_service)


@pytest.fixture
def anki_forum_enricher(snapshot_dir: SnapshotDir, anki_forum_service: AnkiForumService) -> AnkiForumEnricher:
    return AnkiForumEnricher(snapshot_dir, anki_forum_service)


@pytest.fixture
def github_repo() -> GithubRepo:
    return GithubRepo(GithubUserName("John"), GithubRepoName("app"))


@pytest.fixture
def aggregator() -> Aggregator:
    return Aggregator()


@pytest.fixture
def json_exporter(snapshot_dir: SnapshotDir) -> JsonExporter:
    return JsonExporter(snapshot_dir.get_final_dir())


@pytest.fixture
def xlsx_exporter(snapshot_dir: SnapshotDir) -> XlsxExporter:
    return XlsxExporter(snapshot_dir.get_final_dir())


@pytest.fixture
def working_dir_backup(working_dir: WorkingDir) -> WorkingDirBackup:
    return WorkingDirBackup(working_dir)


@pytest.fixture
def hugging_face_client() -> HuggingFaceClient:
    return Mock()


@pytest.fixture
def working_dir_initializer(working_dir: WorkingDir, hugging_face_client: HuggingFaceClient,
                            working_dir_backup: WorkingDirBackup) -> WorkingDirInitializer:
    return WorkingDirInitializer(working_dir, hugging_face_client, working_dir_backup)


@pytest.fixture
def facade(working_dir: WorkingDir, hugging_face_client: HuggingFaceClient) -> Facade:
    return Facade(working_dir, hugging_face_client)


@pytest.fixture
def script_version() -> ScriptVersion:
    return ScriptVersion("0.12.0")


@pytest.fixture
def raw_metadata(script_version: ScriptVersion) -> RawMetadata:
    return RawMetadata(start_timestamp=datetime(2025, 10, 25), script_version=script_version)


@pytest.fixture
def dataset_snapshot_metadata(snapshot_dir: SnapshotDir, script_version: ScriptVersion,
                              report_date: ReportDate) -> DatasetSnapshotMetadata:
    return DatasetMetadata.create_dataset_snapshot_metadata(snapshot_dir, script_version, report_date)


@pytest.fixture
def report_date() -> ReportDate:
    return ReportDate(datetime(2026, 4, 25, 14, 25, 45))
