import logging
from datetime import datetime, timezone
from logging import Logger
from unittest.mock import Mock

from anki_addons_dataset.collector.ankiforum.ankiforum_enricher import AnkiForumEnricher
from anki_addons_dataset.collector.ankiforum.ankiforum_service import AnkiForumService
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId, AddonPage, GithubInfo, AddonInfos, \
    AnkiForumInfo, TopicSlug, TopicId, LastPostedAt, URL, PostsCount, LanguageName, GithubRepo, GithubUserName, \
    GithubRepoName

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
            name="NoteSize",
            addon_page="https://ankiweb.net/shared/info/1188705668",
            rating=4,
            update_date="2023-03-15",
            versions="1.0.0"
        ),
        page=AddonPage(
            like_number=0,
            dislike_number=0,
            versions=[],
            other_links=[],
            anki_forum_url=URL('https://forums.ankiweb.net/t/note-size-addon-support/46001')
        ),
        github=GithubInfo(
            github_links=[],
            github_repo=GithubRepo(GithubUserName("John"), GithubRepoName("app")),
            languages=[LanguageName("Python"), LanguageName("Rust")],
            stars=3,
            last_commit=datetime(2023, 3, 15, 12, 0),
            action_count=5,
            tests_count=7
        ),
        forum=AnkiForumInfo(
            topic_slug=TopicSlug("note-size-addon-support"),
            topic_id=TopicId(46001),
            last_posted_at=LastPostedAt(datetime(2023, 9, 10, 12, 0, 0, 0, tzinfo=timezone.utc)),
            posts_count=PostsCount(42)
        )
    )

    assert act_addon_infos == [exp_addon_info]
