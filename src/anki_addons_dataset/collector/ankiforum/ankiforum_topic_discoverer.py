import copy
import logging
from logging import Logger
from typing import Optional

from pydiscourse.exceptions import DiscourseClientError

from anki_addons_dataset.collector.ai.question.ai_forum_verifier import AiForumAnswer, AiForumVerifier
from anki_addons_dataset.collector.ankiforum.ankiforum_service import AnkiForumService
from anki_addons_dataset.collector.ankiforum.ankiforum_title_matcher import AnkiForumTitleCandidate, \
    AnkiForumTitleMatcher
from anki_addons_dataset.collector.ankiforum.ankiforum_topic import AnkiForumTopic
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AnkiForumCategoryTopic, \
    AnkiForumInfo, AnkiForumTopicContent, AnkiForumTopicSource

log: Logger = logging.getLogger(__name__)


class AnkiForumTopicDiscoverer:
    def __init__(self, anki_forum_service: AnkiForumService, ai_forum_verifier: Optional[AiForumVerifier]):
        self.__anki_forum_service: AnkiForumService = anki_forum_service
        self.__ai_forum_verifier: Optional[AiForumVerifier] = ai_forum_verifier

    def discover(self, addon_infos: AddonInfos) -> AddonInfos:
        topics: list[AnkiForumCategoryTopic] = self.__anki_forum_service.get_category_topics()
        if not topics:
            log.info("No forum category topics in the snapshot")
            return addon_infos
        candidates: dict[AddonId, list[AnkiForumTitleCandidate]] = AnkiForumTitleMatcher.find_candidates(
            addon_infos, topics)
        if self.__ai_forum_verifier is None:
            self.__download_candidates(addon_infos, candidates)
            return addon_infos
        return self.__attach_verified(addon_infos, candidates)

    def __download_candidates(self, addon_infos: AddonInfos,
                              candidates: dict[AddonId, list[AnkiForumTitleCandidate]]) -> None:
        # A most_linked topic may be rejected by the AI step, which runs offline and needs the replacement cached.
        open_addons: list[AddonInfo] = [
            addon_info for addon_info in addon_infos
            if addon_info.forum is None or addon_info.forum.topic_source == AnkiForumTopicSource.MOST_LINKED]
        topics: dict[int, AnkiForumCategoryTopic] = {
            candidate.topic.id: candidate.topic
            for addon_info in open_addons for candidate in candidates.get(addon_info.header.id, [])}
        log.info(f"Downloading {len(topics)} forum topics matched by title")
        for topic in topics.values():
            try:
                self.__anki_forum_service.get_topic_content(topic.slug, topic.id)
            except DiscourseClientError as e:
                log.warning(f"Cannot download forum topic {topic.slug}/{topic.id}: {e}")

    def __attach_verified(self, addon_infos: AddonInfos,
                          candidates: dict[AddonId, list[AnkiForumTitleCandidate]]) -> AddonInfos:
        result: list[AddonInfo] = [self.__attach(addon_info, candidates.get(addon_info.header.id, []))
                                   if addon_info.forum is None else addon_info for addon_info in addon_infos]
        attached: int = sum(1 for before, after in zip(addon_infos, result) if before.forum is None and after.forum)
        log.info(f"Forum topics attached by title match: {attached}")
        return AddonInfos(result)

    def __attach(self, addon_info: AddonInfo, candidates: list[AnkiForumTitleCandidate]) -> AddonInfo:
        for candidate in candidates:
            if self.__is_own_topic(addon_info, candidate.topic):
                return copy.replace(addon_info, forum=self.__forum_info(candidate.topic))
        return addon_info

    def __is_own_topic(self, addon_info: AddonInfo, topic: AnkiForumCategoryTopic) -> bool:
        content: Optional[AnkiForumTopicContent] = self.__anki_forum_service.get_topic_content(topic.slug, topic.id)
        if content is None:
            return False
        try:
            answer: Optional[AiForumAnswer] = self.__ai_forum_verifier.verify_title_match(addon_info, content)
        except Exception as e:
            raise RuntimeError(f"Cannot verify forum topic {topic.id} of addon: {addon_info.header.id}") from e
        return answer is not None and answer.own

    def __forum_info(self, topic: AnkiForumCategoryTopic) -> AnkiForumInfo:
        return AnkiForumInfo(AnkiForumTopic.build_topic_url(topic.slug, topic.id), topic.slug, topic.id,
                             self.__anki_forum_service.get_last_posted_at(topic.slug, topic.id),
                             self.__anki_forum_service.get_posts_count(topic.slug, topic.id),
                             AnkiForumTopicSource.TITLE_MATCH)
