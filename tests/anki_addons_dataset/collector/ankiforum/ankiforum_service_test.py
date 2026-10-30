from unittest.mock import MagicMock

import pytest
from pydiscourse import DiscourseClient
from pytest_mock import MockerFixture

from anki_addons_dataset.collector.ankiforum.ankiforum_service import AnkiForumService
from anki_addons_dataset.common.data_types import TopicId, TopicSlug, LastPostedAt, PostsCount, AnkiForumTopicContent, \
    AnkiForumPost, URL, AnkiForumCategoryTopic
from anki_addons_dataset.common.working_dir import SnapshotDir


def test_get_last_posted_at(anki_forum_service: AnkiForumService, discourse_client: DiscourseClient,
                            topic_slug: TopicSlug, topic_id: TopicId, last_posted_at: LastPostedAt,
                            mocker: MockerFixture):
    method_object: MagicMock = mocker.patch.object(discourse_client, 'topic', return_value={
        'last_posted_at': '2023-09-10T12:00:00.000Z'
    })
    assert anki_forum_service.get_last_posted_at(topic_slug, topic_id) == last_posted_at  # from DiscourseClient
    assert anki_forum_service.get_last_posted_at(topic_slug, topic_id) == last_posted_at  # from SnapshotDir
    method_object.assert_called_once_with(topic_slug, topic_id, override_request_kwargs={"allow_redirects": True})


def test_get_last_posted_at_none(anki_forum_service: AnkiForumService, discourse_client: DiscourseClient,
                                 topic_slug: TopicSlug, topic_id: TopicId, mocker: MockerFixture):
    method_object: MagicMock = mocker.patch.object(discourse_client, 'topic', return_value=None)
    assert anki_forum_service.get_last_posted_at(topic_slug, topic_id) is None  # from DiscourseClient
    assert anki_forum_service.get_last_posted_at(topic_slug, topic_id) is None  # from SnapshotDir
    method_object.assert_called_once_with(topic_slug, topic_id, override_request_kwargs={"allow_redirects": True})


def test_get_last_posted_at_offline(snapshot_dir: SnapshotDir, discourse_client: DiscourseClient,
                                    topic_slug: TopicSlug, topic_id: TopicId):
    offline: bool = True
    anki_forum_service: AnkiForumService = AnkiForumService(discourse_client, snapshot_dir, offline)
    assert anki_forum_service.get_last_posted_at(topic_slug, topic_id) is None


def test_get_posts_count(anki_forum_service: AnkiForumService, discourse_client: DiscourseClient,
                         topic_slug: TopicSlug, topic_id: TopicId, mocker: MockerFixture):
    method_object: MagicMock = mocker.patch.object(discourse_client, 'topic', return_value={
        'posts_count': '42'
    })
    exp_post_count: PostsCount = PostsCount(42)
    assert anki_forum_service.get_posts_count(topic_slug, topic_id) == exp_post_count  # from DiscourseClient
    assert anki_forum_service.get_posts_count(topic_slug, topic_id) == exp_post_count  # from SnapshotDir
    method_object.assert_called_once_with(topic_slug, topic_id, override_request_kwargs={"allow_redirects": True})


def test_get_posts_count_none(anki_forum_service: AnkiForumService, discourse_client: DiscourseClient,
                              topic_slug: TopicSlug, topic_id: TopicId, mocker: MockerFixture):
    method_object: MagicMock = mocker.patch.object(discourse_client, 'topic', return_value=None)
    assert anki_forum_service.get_posts_count(topic_slug, topic_id) is None  # from DiscourseClient
    assert anki_forum_service.get_posts_count(topic_slug, topic_id) is None  # from SnapshotDir
    method_object.assert_called_once_with(topic_slug, topic_id, override_request_kwargs={"allow_redirects": True})


def test_get_posts_count_offline(snapshot_dir: SnapshotDir, discourse_client: DiscourseClient,
                                 topic_slug: TopicSlug, topic_id: TopicId):
    offline: bool = True
    anki_forum_service: AnkiForumService = AnkiForumService(discourse_client, snapshot_dir, offline)
    assert anki_forum_service.get_posts_count(topic_slug, topic_id) is None


def test_get_topic_content(anki_forum_service: AnkiForumService, discourse_client: DiscourseClient,
                           topic_slug: TopicSlug, topic_id: TopicId, mocker: MockerFixture):
    mocker.patch.object(discourse_client, 'topic', return_value={
        'title': 'Note Size addon support',
        'posts_count': 42,
        'details': {'created_by': {'username': 'author'}},
        'post_stream': {'posts': [
            {'post_number': 1, 'username': 'author', 'cooked': '<p>Support for <b>Note Size</b>.</p>'},
            {'post_number': 2, 'username': 'user',
             'cooked': '<p>Try <a href="https://ankiweb.net/shared/info/1188705668">this</a></p>'},
        ]}
    })
    assert anki_forum_service.get_topic_content(topic_slug, topic_id) == AnkiForumTopicContent(
        'Note Size addon support', 'author', 42, [
            AnkiForumPost(1, 'author', 'Support for Note Size .', []),
            AnkiForumPost(2, 'user', 'Try this', [URL('https://ankiweb.net/shared/info/1188705668')]),
        ])


def test_get_topic_content_none(anki_forum_service: AnkiForumService, discourse_client: DiscourseClient,
                                topic_slug: TopicSlug, topic_id: TopicId, mocker: MockerFixture):
    mocker.patch.object(discourse_client, 'topic', return_value=None)
    assert anki_forum_service.get_topic_content(topic_slug, topic_id) is None


def __category_page(topics: list[dict], more: bool) -> dict:
    topic_list: dict = {'topics': topics}
    if more:
        topic_list['more_topics_url'] = '/c/anki/add-ons/11?page=1'
    return {'topic_list': topic_list}


def test_get_category_topics(anki_forum_service: AnkiForumService, discourse_client: DiscourseClient,
                             snapshot_dir: SnapshotDir, mocker: MockerFixture):
    topic_1: dict = {'id': 1, 'slug': 'one', 'title': 'One [Official thread]', 'posts_count': 3}
    topic_2: dict = {'id': 2, 'slug': 'two', 'title': 'Two', 'posts_count': 1}
    method_object: MagicMock = mocker.patch.object(discourse_client, 'category_topics', side_effect=[
        __category_page([topic_1, topic_2], True), __category_page([topic_1], False)])
    exp_topics: list[AnkiForumCategoryTopic] = [
        AnkiForumCategoryTopic(TopicId(1), TopicSlug('one'), 'One [Official thread]', PostsCount(3)),
        AnkiForumCategoryTopic(TopicId(2), TopicSlug('two'), 'Two', PostsCount(1))]
    assert anki_forum_service.get_category_topics() == exp_topics  # from DiscourseClient
    assert anki_forum_service.get_category_topics() == exp_topics  # from SnapshotDir
    assert [call.kwargs['page'] for call in method_object.call_args_list] == [0, 1]
    assert (snapshot_dir.get_raw_dir() / "3-forum" / "category" / "11.json").exists()


def test_get_category_topics_stops_on_an_empty_page(anki_forum_service: AnkiForumService,
                                                    discourse_client: DiscourseClient, mocker: MockerFixture):
    method_object: MagicMock = mocker.patch.object(discourse_client, 'category_topics',
                                                   return_value=__category_page([], True))
    assert anki_forum_service.get_category_topics() == []
    method_object.assert_called_once()


def test_get_category_topics_failure_writes_no_file(anki_forum_service: AnkiForumService,
                                                    discourse_client: DiscourseClient, snapshot_dir: SnapshotDir,
                                                    mocker: MockerFixture):
    topic: dict = {'id': 1, 'slug': 'one', 'title': 'One', 'posts_count': 3}
    mocker.patch.object(discourse_client, 'category_topics',
                        side_effect=[__category_page([topic], True), RuntimeError("boom")])
    with pytest.raises(RuntimeError):
        anki_forum_service.get_category_topics()
    assert not (snapshot_dir.get_raw_dir() / "3-forum" / "category" / "11.json").exists()


def test_get_category_topics_offline(snapshot_dir: SnapshotDir, discourse_client: DiscourseClient,
                                     mocker: MockerFixture):
    method_object: MagicMock = mocker.patch.object(discourse_client, 'category_topics')
    assert AnkiForumService(discourse_client, snapshot_dir, True).get_category_topics() == []
    method_object.assert_not_called()


def test_get_category_topics_offline_reads_the_file(anki_forum_service: AnkiForumService,
                                                    discourse_client: DiscourseClient, snapshot_dir: SnapshotDir,
                                                    mocker: MockerFixture):
    topic: dict = {'id': 1, 'slug': 'one', 'title': 'One', 'posts_count': 3}
    mocker.patch.object(discourse_client, 'category_topics', return_value=__category_page([topic], False))
    online_topics: list[AnkiForumCategoryTopic] = anki_forum_service.get_category_topics()
    assert AnkiForumService(discourse_client, snapshot_dir, True).get_category_topics() == online_topics
