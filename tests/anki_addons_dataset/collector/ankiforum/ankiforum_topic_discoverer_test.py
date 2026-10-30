from dataclasses import replace
from typing import Optional
from unittest.mock import Mock

import pytest
from pydiscourse.exceptions import DiscourseClientError

from anki_addons_dataset.collector.ai.question.ai_forum_verifier import AiForumAnswer, AiForumVerifier
from anki_addons_dataset.collector.ankiforum.ankiforum_service import AnkiForumService
from anki_addons_dataset.collector.ankiforum.ankiforum_topic_discoverer import AnkiForumTopicDiscoverer
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AddonTitle, AnkiForumCategoryTopic, \
    AnkiForumInfo, AnkiForumTopicContent, AnkiForumTopicSource, LastPostedAt, PostsCount, TopicId, TopicSlug, URL

marked_topic: AnkiForumCategoryTopic = AnkiForumCategoryTopic(
    TopicId(1), TopicSlug("image-search-official"), "Image Search [Official Thread]", PostsCount(2))
plain_topic: AnkiForumCategoryTopic = AnkiForumCategoryTopic(
    TopicId(2), TopicSlug("image-search"), "Image Search", PostsCount(9))
content: AnkiForumTopicContent = AnkiForumTopicContent("Image Search [Official Thread]", "author", 2, [])


@pytest.fixture
def anki_forum_service(last_posted_at: LastPostedAt) -> Mock:
    service: Mock = Mock(spec=AnkiForumService)
    service.get_category_topics.return_value = [plain_topic, marked_topic]
    service.get_topic_content.return_value = content
    service.get_last_posted_at.return_value = last_posted_at
    service.get_posts_count.return_value = PostsCount(2)
    return service


def __addon_infos(addon_info: AddonInfo, forum: Optional[AnkiForumInfo] = None) -> AddonInfos:
    return AddonInfos([replace(addon_info, forum=forum, header=replace(
        addon_info.header, id=AddonId(10), title=AddonTitle("Image Search")))])


def __verifier(*answers: Optional[AiForumAnswer]) -> Mock:
    verifier: Mock = Mock(spec=AiForumVerifier)
    verifier.verify_title_match.side_effect = list(answers)
    return verifier


def test_yes_attaches_the_topic(anki_forum_service: Mock, addon_info: AddonInfo, last_posted_at: LastPostedAt):
    verifier: Mock = __verifier(AiForumAnswer(True))
    result: AddonInfos = AnkiForumTopicDiscoverer(anki_forum_service, verifier).discover(__addon_infos(addon_info))
    assert result[0].forum == AnkiForumInfo(
        URL("https://forums.ankiweb.net/t/image-search-official/1"), TopicSlug("image-search-official"), TopicId(1),
        last_posted_at, PostsCount(2), AnkiForumTopicSource.TITLE_MATCH)
    verifier.verify_title_match.assert_called_once()


def test_no_tries_the_next_candidate(anki_forum_service: Mock, addon_info: AddonInfo):
    verifier: Mock = __verifier(AiForumAnswer(False), AiForumAnswer(True))
    result: AddonInfos = AnkiForumTopicDiscoverer(anki_forum_service, verifier).discover(__addon_infos(addon_info))
    assert result[0].forum.topic_id == 2


def test_no_for_every_candidate_attaches_nothing(anki_forum_service: Mock, addon_info: AddonInfo):
    verifier: Mock = __verifier(AiForumAnswer(False), AiForumAnswer(False))
    result: AddonInfos = AnkiForumTopicDiscoverer(anki_forum_service, verifier).discover(__addon_infos(addon_info))
    assert result[0].forum is None


def test_missing_answer_attaches_nothing(anki_forum_service: Mock, addon_info: AddonInfo):
    verifier: Mock = __verifier(None, None)
    result: AddonInfos = AnkiForumTopicDiscoverer(anki_forum_service, verifier).discover(__addon_infos(addon_info))
    assert result[0].forum is None


def test_uncached_topic_is_not_verified(anki_forum_service: Mock, addon_info: AddonInfo):
    anki_forum_service.get_topic_content.return_value = None
    verifier: Mock = __verifier()
    result: AddonInfos = AnkiForumTopicDiscoverer(anki_forum_service, verifier).discover(__addon_infos(addon_info))
    assert result[0].forum is None
    verifier.verify_title_match.assert_not_called()


def test_addon_with_a_topic_is_kept(anki_forum_service: Mock, addon_info: AddonInfo):
    forum: AnkiForumInfo = AnkiForumInfo(URL("https://forums.ankiweb.net/t/other/9"), TopicSlug("other"), TopicId(9),
                                         None, None, AnkiForumTopicSource.AI)
    verifier: Mock = __verifier()
    result: AddonInfos = AnkiForumTopicDiscoverer(anki_forum_service, verifier).discover(
        __addon_infos(addon_info, forum))
    assert result[0].forum == forum
    verifier.verify_title_match.assert_not_called()


def test_snapshot_without_category_is_unchanged(anki_forum_service: Mock, addon_info: AddonInfo):
    anki_forum_service.get_category_topics.return_value = []
    addon_infos: AddonInfos = __addon_infos(addon_info)
    verifier: Mock = __verifier()
    assert AnkiForumTopicDiscoverer(anki_forum_service, verifier).discover(addon_infos) is addon_infos
    verifier.verify_title_match.assert_not_called()


def test_verifier_failure_names_the_addon(anki_forum_service: Mock, addon_info: AddonInfo):
    verifier: Mock = Mock(spec=AiForumVerifier)
    verifier.verify_title_match.side_effect = ValueError("boom")
    with pytest.raises(RuntimeError, match="Cannot verify forum topic 1 of addon: 10"):
        AnkiForumTopicDiscoverer(anki_forum_service, verifier).discover(__addon_infos(addon_info))


def test_download_fetches_candidates_and_attaches_nothing(anki_forum_service: Mock, addon_info: AddonInfo):
    addon_infos: AddonInfos = __addon_infos(addon_info)
    assert AnkiForumTopicDiscoverer(anki_forum_service, None).discover(addon_infos) is addon_infos
    fetched: set[int] = {call.args[1] for call in anki_forum_service.get_topic_content.call_args_list}
    assert fetched == {1, 2}


def test_download_fetches_candidates_of_a_most_linked_addon(anki_forum_service: Mock, addon_info: AddonInfo):
    forum: AnkiForumInfo = AnkiForumInfo(URL("https://forums.ankiweb.net/t/other/9"), TopicSlug("other"), TopicId(9),
                                         None, None, AnkiForumTopicSource.MOST_LINKED)
    AnkiForumTopicDiscoverer(anki_forum_service, None).discover(__addon_infos(addon_info, forum))
    assert anki_forum_service.get_topic_content.call_count == 2


def test_download_skips_candidates_of_a_decided_addon(anki_forum_service: Mock, addon_info: AddonInfo):
    forum: AnkiForumInfo = AnkiForumInfo(URL("https://forums.ankiweb.net/t/other/9"), TopicSlug("other"), TopicId(9),
                                         None, None, AnkiForumTopicSource.CONTACT_AUTHOR)
    AnkiForumTopicDiscoverer(anki_forum_service, None).discover(__addon_infos(addon_info, forum))
    anki_forum_service.get_topic_content.assert_not_called()


def test_download_survives_a_deleted_topic(anki_forum_service: Mock, addon_info: AddonInfo):
    anki_forum_service.get_topic_content.side_effect = [DiscourseClientError("gone"), content]
    AnkiForumTopicDiscoverer(anki_forum_service, None).discover(__addon_infos(addon_info))
    assert anki_forum_service.get_topic_content.call_count == 2
