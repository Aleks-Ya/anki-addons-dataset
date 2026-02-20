from typing import Optional
from unittest.mock import MagicMock

from pytest import raises
from pydiscourse import DiscourseClient
from pytest_mock import MockerFixture

from anki_addons_dataset.collector.ankiforum.ankiforum_service import AnkiForumService
from anki_addons_dataset.common.data_types import URL, TopicId, TopicSlug, LastPostedAt
from anki_addons_dataset.common.working_dir import VersionDir


def test_extract_topic_slug(anki_forum_service: AnkiForumService, topic_slug: TopicSlug):
    anki_forum_url: URL = URL("https://forums.ankiweb.net/t/note-size-addon-support/46001")
    act: Optional[TopicSlug] = anki_forum_service.extract_topic_slug(anki_forum_url)
    assert act == topic_slug


def test_extract_topic_slug2(anki_forum_service: AnkiForumService, topic_slug: TopicSlug):
    anki_forum_url: URL = URL(
        "https://forums.ankiweb.net/t/add-on-support-thread-bulk-image-downloader-for-anki-googleapi-webp-during-review-by-shige/43541")
    act: Optional[TopicSlug] = anki_forum_service.extract_topic_slug(anki_forum_url)
    assert act == TopicSlug(
        "add-on-support-thread-bulk-image-downloader-for-anki-googleapi-webp-during-review-by-shige")


def test_extract_topic_slug_none(anki_forum_service: AnkiForumService):
    act: Optional[TopicSlug] = anki_forum_service.extract_topic_slug(None)
    assert act is None


def test_extract_topic_slug_invalid(anki_forum_service: AnkiForumService):
    anki_forum_url: URL = URL("https://www.linux.org/threads/system-will-not-boot.62847/")
    with raises(ValueError) as ex_info:
        anki_forum_service.extract_topic_slug(anki_forum_url)
    e: ValueError = ex_info.value
    assert "Cannot extract Topic Slug from Anki Forum Topic URL: 'https://www.linux.org/threads/system-will-not-boot.62847/'" in e.args


def test_extract_topic_id(anki_forum_service: AnkiForumService, topic_id: TopicId):
    anki_forum_url: URL = URL("https://forums.ankiweb.net/t/note-size-addon-support/46001")
    act: Optional[TopicId] = anki_forum_service.extract_topic_id(anki_forum_url)
    assert act == topic_id


def test_extract_topic_id_none(anki_forum_service: AnkiForumService):
    act: Optional[TopicId] = anki_forum_service.extract_topic_id(None)
    assert act is None


def test_extract_topic_id_invalid(anki_forum_service: AnkiForumService):
    anki_forum_url: URL = URL("https://www.linux.org/threads/system-will-not-boot.62847/")
    with raises(ValueError) as ex_info:
        anki_forum_service.extract_topic_id(anki_forum_url)
    e: ValueError = ex_info.value
    assert "Cannot extract Topic ID from Anki Forum Topic URL: 'https://www.linux.org/threads/system-will-not-boot.62847/'" in e.args


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
