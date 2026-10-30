import difflib
import re
from dataclasses import dataclass

from anki_addons_dataset.common.data_types import AddonId, AddonInfos, AnkiForumCategoryTopic, TopicId


@dataclass(frozen=True)
class AnkiForumTitleCandidate:
    topic: AnkiForumCategoryTopic
    marked: bool


class AnkiForumTitleMatcher:
    __marker: re.Pattern[str] = re.compile(
        r"\b(official|support)\s+(support\s+)?(thread|topic|page|post)\b"
        r"|\[\s*official\b[^\]]*\]|\(\s*official\b[^)]*\)|\[\s*support\b[^\]]*\]|\(\s*support\b[^)]*\)"
        r"|\[\s*add-?on\s*\]|\bofficial\s+support\b",
        re.IGNORECASE)
    __question: re.Pattern[str] = re.compile(
        r"\?|\b(not working|doesn'?t work|does not work|error|bug|issue|problem|how to|how do|request|help|broken|"
        r"looking for|is there|anyone|can'?t|cannot|unable|crash|fail)",
        re.IGNORECASE)
    __filler: re.Pattern[str] = re.compile(
        r"\b(add[\s-]?ons?|plugins?|threads?|support|official|anki|2\.1|the|new|page|topic)\b",
        re.IGNORECASE)
    __punctuation: re.Pattern[str] = re.compile(r"[\W_]")
    __close_cutoff: float = 0.85
    __shortlist_cutoff: float = 0.5
    __shortlist_size: int = 3

    @classmethod
    def find_candidates(cls, addon_infos: AddonInfos, topics: list[AnkiForumCategoryTopic]
                        ) -> dict[AddonId, list[AnkiForumTitleCandidate]]:
        addons_by_title: dict[str, list[AddonId]] = {}
        for addon_info in addon_infos:
            title: str = cls.__normalize(addon_info.header.title)
            if title:
                addons_by_title.setdefault(title, []).append(addon_info.header.id)
        titles: list[str] = list(addons_by_title)
        claimed: set[TopicId] = {addon_info.forum.topic_id for addon_info in addon_infos
                                 if addon_info.forum and addon_info.forum.topic_id}
        candidates: dict[AddonId, list[AnkiForumTitleCandidate]] = {}
        for topic in topics:
            marked: bool = bool(cls.__marker.search(topic.title))
            if topic.id in claimed or (not marked and cls.__question.search(topic.title)):
                continue
            for title in cls.__matching_titles(cls.__normalize(topic.title), marked, addons_by_title, titles):
                for addon_id in addons_by_title[title]:
                    candidates.setdefault(addon_id, []).append(AnkiForumTitleCandidate(topic, marked))
        return {addon_id: sorted(addon_candidates, key=cls.__preference)
                for addon_id, addon_candidates in candidates.items()}

    @classmethod
    def __matching_titles(cls, topic_title: str, marked: bool, addons_by_title: dict[str, list[AddonId]],
                          titles: list[str]) -> list[str]:
        if not topic_title:
            return []
        if topic_title in addons_by_title:
            return [topic_title]
        close_titles: list[str] = difflib.get_close_matches(topic_title, titles, n=1, cutoff=cls.__close_cutoff)
        if close_titles or not marked:
            return close_titles
        return difflib.get_close_matches(topic_title, titles, n=cls.__shortlist_size, cutoff=cls.__shortlist_cutoff)

    @classmethod
    def __normalize(cls, title: str) -> str:
        without_marker: str = cls.__marker.sub(" ", title)
        without_filler: str = cls.__filler.sub(" ", without_marker)
        return " ".join(cls.__punctuation.sub(" ", without_filler).lower().split())

    @staticmethod
    def __preference(candidate: AnkiForumTitleCandidate) -> tuple[bool, int, int]:
        return not candidate.marked, -candidate.topic.posts_count, candidate.topic.id
