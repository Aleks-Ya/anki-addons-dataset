from dataclasses import replace

import pytest

from anki_addons_dataset.collector.ankiforum.ankiforum_title_matcher import AnkiForumTitleMatcher, \
    AnkiForumTitleCandidate
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AddonTitle, AnkiForumCategoryTopic, \
    AnkiForumInfo, PostsCount, TopicId, TopicSlug, URL


def __topic(topic_id: int, title: str, posts_count: int = 1) -> AnkiForumCategoryTopic:
    return AnkiForumCategoryTopic(TopicId(topic_id), TopicSlug(f"slug-{topic_id}"), title, PostsCount(posts_count))


@pytest.fixture
def make_addon_infos(addon_info: AddonInfo):
    def make(titles: dict[int, str]) -> AddonInfos:
        return AddonInfos([replace(addon_info, forum=None,
                                   header=replace(addon_info.header, id=AddonId(addon_id), title=AddonTitle(title)))
                           for addon_id, title in titles.items()])

    return make


def test_marked_topic_matches_by_title(make_addon_infos):
    topic: AnkiForumCategoryTopic = __topic(1, "Puppy Reinforcement [Official Support Thread]")
    candidates = AnkiForumTitleMatcher.find_candidates(make_addon_infos({10: "Puppy Reinforcement"}), [topic])
    assert candidates == {10: [AnkiForumTitleCandidate(topic, True)]}


def test_unmarked_topic_matches_by_title(make_addon_infos):
    topic: AnkiForumCategoryTopic = __topic(1, "Duplicate Selected Notes add-on")
    candidates = AnkiForumTitleMatcher.find_candidates(make_addon_infos({10: "Duplicate Selected Notes"}), [topic])
    assert candidates == {10: [AnkiForumTitleCandidate(topic, False)]}


def test_close_title_matches(make_addon_infos):
    topic: AnkiForumCategoryTopic = __topic(1, "Enhanced Cloze 2.1")
    candidates = AnkiForumTitleMatcher.find_candidates(make_addon_infos({10: "Enhanced Cloze (for Anki 2.1)"}), [topic])
    assert list(candidates) == [10]


def test_unmarked_question_is_dropped(make_addon_infos):
    addon_infos: AddonInfos = make_addon_infos({10: "Skip Anki home"})
    topics: list[AnkiForumCategoryTopic] = [__topic(1, "Bug? Skip Anki home"), __topic(2, "Skip Anki home not working")]
    assert AnkiForumTitleMatcher.find_candidates(addon_infos, topics) == {}


def test_marked_question_is_kept(make_addon_infos):
    topic: AnkiForumCategoryTopic = __topic(1, "Error Finder [Support Thread]")
    assert list(AnkiForumTitleMatcher.find_candidates(make_addon_infos({10: "Error Finder"}), [topic])) == [10]


def test_unrelated_unmarked_topic_does_not_match(make_addon_infos):
    addon_infos: AddonInfos = make_addon_infos({10: "Deck Completion Column"})
    assert AnkiForumTitleMatcher.find_candidates(addon_infos, [__topic(1, "Wiktionary Add-on")]) == {}


def test_marked_topic_without_a_close_title_gets_a_shortlist(make_addon_infos):
    addon_infos: AddonInfos = make_addon_infos({10: "Deck Completion Line", 20: "Deck Completion Bar",
                                                30: "Deck Completion Table", 40: "Deck Completion Chart",
                                                50: "Wiktionary"})
    topic: AnkiForumCategoryTopic = __topic(1, "Completion of Deck [Support Thread]")
    candidates = AnkiForumTitleMatcher.find_candidates(addon_infos, [topic])
    assert len(candidates) == 3
    assert 50 not in candidates


def test_topic_matches_every_addon_with_the_same_title(make_addon_infos):
    addon_infos: AddonInfos = make_addon_infos({10: "Image Search", 20: "Image Search"})
    candidates = AnkiForumTitleMatcher.find_candidates(addon_infos, [__topic(1, "Image Search")])
    assert list(candidates) == [10, 20]


def test_topic_of_another_addon_is_skipped(make_addon_infos):
    addon_infos: AddonInfos = make_addon_infos({10: "Image Search", 20: "Other"})
    linked: AddonInfo = replace(addon_infos[1], forum=AnkiForumInfo(
        URL("https://forums.ankiweb.net/t/slug-1/1"), TopicSlug("slug-1"), TopicId(1), None, None))
    candidates = AnkiForumTitleMatcher.find_candidates(AddonInfos([addon_infos[0], linked]),
                                                       [__topic(1, "Image Search")])
    assert candidates == {}


def test_match_ignores_whether_the_addon_already_has_a_topic(make_addon_infos):
    addon_infos: AddonInfos = make_addon_infos({10: "Image Search"})
    linked: AddonInfo = replace(addon_infos[0], forum=AnkiForumInfo(
        URL("https://forums.ankiweb.net/t/slug-9/9"), TopicSlug("slug-9"), TopicId(9), None, None))
    assert list(AnkiForumTitleMatcher.find_candidates(AddonInfos([linked]), [__topic(1, "Image Search")])) == [10]


def test_candidates_prefer_a_marker_then_the_most_posts(make_addon_infos):
    addon_infos: AddonInfos = make_addon_infos({10: "Image Search"})
    topics: list[AnkiForumCategoryTopic] = [__topic(1, "Image Search", 5), __topic(2, "Image Search add-on", 50),
                                            __topic(3, "Image Search [Official Thread]", 2)]
    candidates = AnkiForumTitleMatcher.find_candidates(addon_infos, topics)
    assert [candidate.topic.id for candidate in candidates[10]] == [3, 2, 1]


def test_title_of_only_filler_words_matches_nothing(make_addon_infos):
    addon_infos: AddonInfos = make_addon_infos({10: "Anki Add-on", 20: "Image Search"})
    topics: list[AnkiForumCategoryTopic] = [__topic(1, "Add-on [Official Thread]"), __topic(2, "Anki addon")]
    assert AnkiForumTitleMatcher.find_candidates(addon_infos, topics) == {}
