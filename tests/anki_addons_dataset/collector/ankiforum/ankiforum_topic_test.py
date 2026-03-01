from typing import Optional

from pytest import raises

from anki_addons_dataset.collector.ankiforum.ankiforum_topic import AnkiForumTopic
from anki_addons_dataset.common.data_types import URL, TopicId, TopicSlug


def test_extract_topic_slug(topic_slug: TopicSlug):
    anki_forum_url: URL = URL("https://forums.ankiweb.net/t/note-size-addon-support/46001")
    act: Optional[TopicSlug] = AnkiForumTopic.extract_topic_slug(anki_forum_url)
    assert act == topic_slug


def test_extract_topic_slug2(topic_slug: TopicSlug):
    anki_forum_url: URL = URL(
        "https://forums.ankiweb.net/t/add-on-support-thread-bulk-image-downloader-for-anki-googleapi-webp-during-review-by-shige/43541")
    act: Optional[TopicSlug] = AnkiForumTopic.extract_topic_slug(anki_forum_url)
    assert act == TopicSlug(
        "add-on-support-thread-bulk-image-downloader-for-anki-googleapi-webp-during-review-by-shige")


def test_extract_topic_slug_none():
    act: Optional[TopicSlug] = AnkiForumTopic.extract_topic_slug(None)
    assert act is None


def test_extract_topic_slug_invalid():
    anki_forum_url: URL = URL("https://www.linux.org/threads/system-will-not-boot.62847/")
    with raises(ValueError) as ex_info:
        AnkiForumTopic.extract_topic_slug(anki_forum_url)
    e: ValueError = ex_info.value
    assert "Cannot extract Topic Slug from Anki Forum Topic URL: 'https://www.linux.org/threads/system-will-not-boot.62847/'" in e.args


def test_extract_topic_id(topic_id: TopicId):
    anki_forum_url: URL = URL("https://forums.ankiweb.net/t/note-size-addon-support/46001")
    act: Optional[TopicId] = AnkiForumTopic.extract_topic_id(anki_forum_url)
    assert act == topic_id


def test_extract_topic_id_none():
    act: Optional[TopicId] = AnkiForumTopic.extract_topic_id(None)
    assert act is None


def test_extract_topic_id_invalid():
    anki_forum_url: URL = URL("https://www.linux.org/threads/system-will-not-boot.62847/")
    with raises(ValueError) as ex_info:
        AnkiForumTopic.extract_topic_id(anki_forum_url)
    e: ValueError = ex_info.value
    assert "Cannot extract Topic ID from Anki Forum Topic URL: 'https://www.linux.org/threads/system-will-not-boot.62847/'" in e.args
