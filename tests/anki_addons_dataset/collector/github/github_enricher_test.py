from datetime import datetime
import logging
from logging import Logger
from unittest.mock import Mock

from anki_addons_dataset.collector.github.github_enricher import GithubEnricher
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.collector.github.handler.repo_info_repo_handler import GithubRepoMeta
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId, AddonPage, GithubRepo, \
    LanguageName, GithubInfo, AddonInfos, AnkiForumInfo, TopicSlug, TopicId, LastPostedAt, PostsCount, AnkiVersion, \
    HtmlStr, URL, AddonRating, UpdateDate, AddonTitle, AddonManifest, SpdxLicense, Topic, DependencyName

log: Logger = logging.getLogger(__name__)


def test_enrich(github_enricher: GithubEnricher, github_service: GithubService, note_size_addon_id: AddonId,
                topic_slug: TopicSlug, topic_id: TopicId, last_posted_at: LastPostedAt, posts_count: PostsCount,
                github_repo: GithubRepo):
    addon_info: AddonInfo = AddonInfo(
        header=AddonHeader(
            id=note_size_addon_id,
            title=AddonTitle("NoteSize"),
            addon_page_url=URL("https://ankiweb.net/shared/info/1188705668"),
            rating=AddonRating(4),
            update_date=UpdateDate("2023-03-15"),
            anki_version=AnkiVersion("1.0.0")
        ),
        page=AddonPage(
            content=HtmlStr("<html><body><h1>Sample addon page content</h1></body></html>"),
            like_number=0,
            dislike_number=0,
            branches=[],
            other_links=[]
        ),
        github=GithubInfo(
            github_links=[],
            github_repo=github_repo,
            languages=[],
            stars=0,
            last_commit=None,
            action_count=0,
            tests_count=0
        ),
        forum=AnkiForumInfo(
            anki_forum_url=None,
            topic_slug=topic_slug,
            topic_id=topic_id,
            last_posted_at=last_posted_at,
            posts_count=posts_count
        )
    )

    last_commit: datetime = datetime(2023, 3, 15, 12, 0, 0, 0)
    pushed_at: datetime = datetime(2023, 3, 16, 10, 0, 0)
    created_at: datetime = datetime(2020, 1, 1, 9, 0, 0)
    manifest: AddonManifest = AddonManifest(package="note_size", name="Note Size", conflicts=["1234567"],
                                             min_point_version=45, max_point_version=None,
                                             homepage="https://example.com", mod=1678900000)
    github_service.get_languages = Mock(return_value={LanguageName("Python"): 5, LanguageName("Rust"): 2})
    github_service.get_stars_count = Mock(return_value=3)
    github_service.get_last_commit = Mock(return_value=last_commit)
    github_service.get_action_count = Mock(return_value=5)
    github_service.get_tests_count = Mock(return_value=7)
    github_service.get_repo_info = Mock(return_value=GithubRepoMeta(
        license=SpdxLicense("MIT"), forks=4, open_issues=2, size_kb=128, topics=[Topic("anki")],
        repo_description="A NoteSize addon", homepage=URL("https://example.com"), archived=False,
        pushed_at=pushed_at, created_at=created_at))
    github_service.get_manifest = Mock(return_value=manifest)
    github_service.get_dependencies = Mock(return_value=[DependencyName("requests"), DependencyName("beautifulsoup4")])
    github_service.get_readme = Mock(return_value="# NoteSize\nExample readme")
    github_service.get_ai_tooling_markers = Mock(return_value=["claude-code"])

    github_enricher.start()
    github_enricher.download_in_background(addon_info)
    github_enricher.wait_download_finish()
    act_addon_infos: AddonInfos = github_enricher.enrich(AddonInfos([addon_info]))

    exp_addon_info: AddonInfo = AddonInfo(
        header=AddonHeader(
            id=note_size_addon_id,
            title=AddonTitle("NoteSize"),
            addon_page_url=URL("https://ankiweb.net/shared/info/1188705668"),
            rating=AddonRating(4),
            update_date=UpdateDate("2023-03-15"),
            anki_version=AnkiVersion("1.0.0")
        ),
        page=AddonPage(
            content=HtmlStr("<html><body><h1>Sample addon page content</h1></body></html>"),
            like_number=0,
            dislike_number=0,
            branches=[],
            other_links=[]
        ),
        github=GithubInfo(
            github_links=[],
            github_repo=github_repo,
            languages=[LanguageName("Python"), LanguageName("Rust")],
            stars=3,
            last_commit=last_commit,
            action_count=5,
            tests_count=7,
            license=SpdxLicense("MIT"),
            forks=4,
            open_issues=2,
            size_kb=128,
            topics=[Topic("anki")],
            repo_description="A NoteSize addon",
            homepage=URL("https://example.com"),
            archived=False,
            pushed_at=pushed_at,
            created_at=created_at,
            primary_language=LanguageName("Python"),
            language_bytes={LanguageName("Python"): 5, LanguageName("Rust"): 2},
            manifest=manifest,
            dependencies=[DependencyName("requests"), DependencyName("beautifulsoup4")],
            readme="# NoteSize\nExample readme",
            ai_tooling_markers=["claude-code"]
        ),
        forum=AnkiForumInfo(
            anki_forum_url=None,
            topic_slug=topic_slug,
            topic_id=topic_id,
            last_posted_at=last_posted_at,
            posts_count=posts_count
        )
    )

    assert act_addon_infos == [exp_addon_info]
