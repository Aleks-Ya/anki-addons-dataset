import copy
import logging
from datetime import datetime, timezone, date
from logging import Logger
from typing import Optional
from unittest.mock import Mock

import pytest

from anki_addons_dataset.collector.ai.question.ai_forum_verifier import AiForumVerifier, AiForumAnswer
from anki_addons_dataset.collector.ankiforum.ankiforum_enricher import AnkiForumEnricher
from anki_addons_dataset.collector.ankiforum.ankiforum_service import AnkiForumService
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId, AddonPage, GithubInfo, AddonInfos, \
    AnkiForumInfo, TopicSlug, TopicId, LastPostedAt, URL, PostsCount, LanguageName, GithubRepo, GithubUserName, \
    GithubRepoName, AnkiVersion, AddonBranch, HtmlStr, AddonRating, UpdateDate, AddonTitle, AddonDescription, \
    AiInfo, AiSummary, AiModel, AiTag, AnkiPointVersion, AnkiVersionKind, AuthorInfo, AnkiForumTopicSource, \
    AnkiForumTopicContent, AnkiForumPost
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


def test_enrich(anki_forum_enricher: AnkiForumEnricher, anki_forum_service: AnkiForumService,
                last_posted_at: LastPostedAt, posts_count: PostsCount, addon_info: AddonInfo, addon_infos: AddonInfos):
    anki_forum_service.get_last_posted_at = Mock(return_value=last_posted_at)
    anki_forum_service.get_posts_count = Mock(return_value=posts_count)
    anki_forum_enricher.start()
    anki_forum_enricher.download_in_background(addon_info)
    anki_forum_enricher.wait_download_finish()
    act_addon_infos: AddonInfos = anki_forum_enricher.enrich(addon_infos)

    exp_addon_info: AddonInfo = AddonInfo(
        header=AddonHeader(
            id=AddonId(1188705668),
            title=AddonTitle("NoteSize"),
            addon_page_url=URL("https://ankiweb.net/shared/info/1188705668"),
            rating=AddonRating(4),
            update_date=UpdateDate("2023-03-15"),
            anki_version=AnkiVersion("25.09.2~"),
            anki_point_version=AnkiPointVersion(250902),
            anki_version_kind=AnkiVersionKind.TESTED
        ),
        page=AddonPage(
            content=HtmlStr("<html><body><h1>Sample addon page content</h1></body></html>"),
            like_number=0,
            dislike_number=0,
            branches=[AddonBranch(min_anki_version=AnkiVersion("24.04.1"),
                                  max_anki_version=AnkiVersion("25.09.2+"),
                                  updated=date(2023, 3, 15),
                                  min_point_version=AnkiPointVersion(240401),
                                  max_point_version=AnkiPointVersion(250902),
                                  max_version_kind=AnkiVersionKind.TESTED)],
            links=[],
            description=AddonDescription("Sample addon description for full text search"),
            ai_declaration_markers=["chatgpt"],
            description_html=HtmlStr("<p>Sample addon <b>description</b> for full text search</p>"),
            description_pre_wrap=True,
            other_items_count=2
        ),
        github=GithubInfo(
            github_links=[],
            github_repo=GithubRepo(GithubUserName("John"), GithubRepoName("app")),
            languages=[LanguageName("Python"), LanguageName("Rust")],
            stars=3,
            last_commit=datetime(2023, 3, 15, 12, 0),
            action_count=5,
            tests_count=7,
            ai_tooling_markers=["claude-code", "cursor"]
        ),
        forum=AnkiForumInfo(
            anki_forum_url=URL('https://forums.ankiweb.net/t/note-size-addon-support/46001'),
            topic_slug=TopicSlug("note-size-addon-support"),
            topic_id=TopicId(46001),
            last_posted_at=LastPostedAt(datetime(2023, 9, 10, 12, 0, 0, 0, tzinfo=timezone.utc)),
            posts_count=PostsCount(42),
            topic_source=AnkiForumTopicSource.CONTACT_AUTHOR
        ),
        ai=AiInfo(
            summary=AiSummary("Shows the size of the collection and of individual notes."),
            model=AiModel("test-model"),
            tags=[AiTag("statistics")]
        ),
        author=AuthorInfo(
            author_id=AddonId(1188705668),
            addon_ids=[AddonId(1188705668), AddonId(1312127886), AddonId(1956435337)]
        )
    )

    assert act_addon_infos == [exp_addon_info]


topic: AnkiForumTopicContent = AnkiForumTopicContent(
    "Note Size addon support", "author", 42, [AnkiForumPost(1, "author", "Support thread.", [])])


def __verified_forum(snapshot_dir: SnapshotDir, anki_forum_service: AnkiForumService, addon_info: AddonInfo,
                     topic_source: AnkiForumTopicSource, answer: Optional[AiForumAnswer],
                     topic_content: Optional[AnkiForumTopicContent] = topic) -> tuple[Optional[AnkiForumInfo], Mock]:
    anki_forum_service.get_last_posted_at = Mock(return_value=None)
    anki_forum_service.get_posts_count = Mock(return_value=PostsCount(42))
    anki_forum_service.get_topic_content = Mock(return_value=topic_content)
    verifier: Mock = Mock(spec=AiForumVerifier)
    verifier.verify = Mock(return_value=answer)
    enricher: AnkiForumEnricher = AnkiForumEnricher(snapshot_dir, anki_forum_service, verifier, offline=True)
    linked_addon_info: AddonInfo = copy.replace(addon_info, forum=copy.replace(addon_info.forum,
                                                                               topic_source=topic_source))
    enricher.start()
    enricher.download_in_background(linked_addon_info)
    enricher.wait_download_finish()
    return enricher.enrich(AddonInfos([linked_addon_info]))[0].forum, verifier


@pytest.mark.parametrize("answer, exp_source", [
    (AiForumAnswer(True), AnkiForumTopicSource.AI),
    (None, AnkiForumTopicSource.MOST_LINKED),
])
def test_most_linked_topic_kept(snapshot_dir: SnapshotDir, anki_forum_service: AnkiForumService,
                                addon_info: AddonInfo, answer: Optional[AiForumAnswer],
                                exp_source: AnkiForumTopicSource):
    forum, verifier = __verified_forum(snapshot_dir, anki_forum_service, addon_info,
                                       AnkiForumTopicSource.MOST_LINKED, answer)
    assert forum.topic_source == exp_source
    assert forum.posts_count == PostsCount(42)
    verifier.verify.assert_called_once()


def test_most_linked_topic_rejected(snapshot_dir: SnapshotDir, anki_forum_service: AnkiForumService,
                                    addon_info: AddonInfo):
    forum, _ = __verified_forum(snapshot_dir, anki_forum_service, addon_info,
                                AnkiForumTopicSource.MOST_LINKED, AiForumAnswer(False))
    assert forum is None


def test_most_linked_topic_without_content_is_kept(snapshot_dir: SnapshotDir, anki_forum_service: AnkiForumService,
                                                   addon_info: AddonInfo):
    forum, verifier = __verified_forum(snapshot_dir, anki_forum_service, addon_info,
                                       AnkiForumTopicSource.MOST_LINKED, AiForumAnswer(False), None)
    assert forum.topic_source == AnkiForumTopicSource.MOST_LINKED
    verifier.verify.assert_not_called()


@pytest.mark.parametrize("topic_source", [AnkiForumTopicSource.CONTACT_AUTHOR, AnkiForumTopicSource.OVERRIDE])
def test_decided_topic_is_not_verified(snapshot_dir: SnapshotDir, anki_forum_service: AnkiForumService,
                                       addon_info: AddonInfo, topic_source: AnkiForumTopicSource):
    forum, verifier = __verified_forum(snapshot_dir, anki_forum_service, addon_info, topic_source,
                                       AiForumAnswer(False))
    assert forum.topic_source == topic_source
    verifier.verify.assert_not_called()
