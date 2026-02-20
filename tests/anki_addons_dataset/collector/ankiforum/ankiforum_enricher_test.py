import logging
from logging import Logger
from unittest.mock import Mock

from anki_addons_dataset.collector.ankiforum.ankiforum_enricher import AnkiForumEnricher
from anki_addons_dataset.collector.ankiforum.ankiforum_service import AnkiForumService
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId, AddonPage, GithubInfo, AddonInfos, \
    AnkiForumInfo, TopicSlug, TopicId, LastPostedAt, URL

log: Logger = logging.getLogger(__name__)


def test_enrich(anki_forum_enricher: AnkiForumEnricher, anki_forum_service: AnkiForumService, anki_forum_url: URL,
                note_size_addon_id: AddonId, topic_slug: TopicSlug, topic_id: TopicId, last_posted_at: LastPostedAt):
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
            other_links=[],
            anki_forum_url=anki_forum_url
        ),
        github=GithubInfo(
            github_links=[],
            github_repo=None,
            languages=[],
            stars=0,
            last_commit=None,
            action_count=0,
            tests_count=0
        ),
        forum=None
    )

    anki_forum_service.get_last_posted_at = Mock(return_value=last_posted_at)
    anki_forum_enricher.start()
    anki_forum_enricher.download_in_background(addon_info)
    anki_forum_enricher.wait_download_finish()
    act_addon_infos: AddonInfos = anki_forum_enricher.enrich(AddonInfos([addon_info]))

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
            other_links=[],
            anki_forum_url=anki_forum_url
        ),
        github=GithubInfo(
            github_links=[],
            github_repo=None,
            languages=[],
            stars=0,
            last_commit=None,
            action_count=0,
            tests_count=0
        ),
        forum=AnkiForumInfo(
            topic_slug=topic_slug,
            topic_id=topic_id,
            last_posted_at=last_posted_at
        )
    )

    assert act_addon_infos == [exp_addon_info]
