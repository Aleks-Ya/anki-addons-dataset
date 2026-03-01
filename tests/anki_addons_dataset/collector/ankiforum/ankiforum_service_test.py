from unittest.mock import MagicMock

from pydiscourse import DiscourseClient
from pytest_mock import MockerFixture

from anki_addons_dataset.collector.ankiforum.ankiforum_service import AnkiForumService
from anki_addons_dataset.common.data_types import TopicId, TopicSlug, LastPostedAt
from anki_addons_dataset.common.working_dir import VersionDir


def test_get_last_posted_at(anki_forum_service: AnkiForumService, discourse_client: DiscourseClient,
                            topic_slug: TopicSlug, topic_id: TopicId, last_posted_at: LastPostedAt,
                            mocker: MockerFixture):
    method_object: MagicMock = mocker.patch.object(discourse_client, 'topic', return_value={
        'last_posted_at': '2023-09-10T12:00:00.000Z'
    })
    assert anki_forum_service.get_last_posted_at(topic_slug, topic_id) == last_posted_at  # from DiscourseClient
    assert anki_forum_service.get_last_posted_at(topic_slug, topic_id) == last_posted_at  # from VersionDir
    method_object.assert_called_once_with(topic_slug, topic_id, override_request_kwargs={"allow_redirects": True})


def test_get_last_posted_at_none(anki_forum_service: AnkiForumService, discourse_client: DiscourseClient,
                                 topic_slug: TopicSlug, topic_id: TopicId, mocker: MockerFixture):
    method_object: MagicMock = mocker.patch.object(discourse_client, 'topic', return_value=None)
    assert anki_forum_service.get_last_posted_at(topic_slug, topic_id) is None  # from DiscourseClient
    assert anki_forum_service.get_last_posted_at(topic_slug, topic_id) is None  # from VersionDir
    method_object.assert_called_once_with(topic_slug, topic_id, override_request_kwargs={"allow_redirects": True})


def test_get_last_posted_at_offline(version_dir: VersionDir, discourse_client: DiscourseClient,
                                    topic_slug: TopicSlug, topic_id: TopicId):
    offline: bool = True
    anki_forum_service: AnkiForumService = AnkiForumService(discourse_client, version_dir, offline)
    assert anki_forum_service.get_last_posted_at(topic_slug, topic_id) is None
