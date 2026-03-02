from datetime import datetime
import logging
from logging import Logger
from unittest.mock import Mock

from anki_addons_dataset.collector.github.github_enricher import GithubEnricher
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId, AddonPage, GithubRepo, \
    LanguageName, GithubInfo, AddonInfos, AnkiForumInfo, TopicSlug, TopicId, LastPostedAt, PostsCount

log: Logger = logging.getLogger(__name__)


def test_enrich(github_enricher: GithubEnricher, github_service: GithubService, note_size_addon_id: AddonId,
                topic_slug: TopicSlug, topic_id: TopicId, last_posted_at: LastPostedAt, posts_count: PostsCount,
                github_repo: GithubRepo):
    addon_info: AddonInfo = AddonInfo(
        header=AddonHeader(
            id=note_size_addon_id,
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
    github_service.get_languages = Mock(return_value={LanguageName("Python"): 5, LanguageName("Rust"): 2})
    github_service.get_stars_count = Mock(return_value=3)
    github_service.get_last_commit = Mock(return_value=last_commit)
    github_service.get_action_count = Mock(return_value=5)
    github_service.get_tests_count = Mock(return_value=7)

    github_enricher.start()
    github_enricher.download_in_background(addon_info)
    github_enricher.wait_download_finish()
    act_addon_infos: AddonInfos = github_enricher.enrich(AddonInfos([addon_info]))

    exp_addon_info: AddonInfo = AddonInfo(
        header=AddonHeader(
            id=note_size_addon_id,
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
            other_links=[]
        ),
        github=GithubInfo(
            github_links=[],
            github_repo=github_repo,
            languages=[LanguageName("Python"), LanguageName("Rust")],
            stars=3,
            last_commit=last_commit,
            action_count=5,
            tests_count=7
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
