import copy
from pathlib import Path
from threading import Lock
from typing import Optional
import logging
from logging import Logger

from anki_addons_dataset.collector.ai.question.ai_forum_verifier import AiForumVerifier, AiForumAnswer
from anki_addons_dataset.collector.ankiforum.ankiforum_service import AnkiForumService
from anki_addons_dataset.collector.ankiforum.ankiforum_topic import AnkiForumTopic
from anki_addons_dataset.collector.enricher import Enricher
from anki_addons_dataset.common.data_types import AddonInfo, AddonId, \
    AnkiForumInfo, TopicSlug, TopicId, LastPostedAt, AddonInfos, PostsCount, URL, AnkiForumTopicSource, \
    AnkiForumTopicContent
from anki_addons_dataset.common.json_helper import JsonHelper
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


class AnkiForumEnricher(Enricher):
    __name: str = "AnkiForum"
    __offline_pool_size: int = 50

    def __init__(self, snapshot_dir: SnapshotDir, anki_forum_service: AnkiForumService,
                 ai_forum_verifier: Optional[AiForumVerifier] = None, offline: bool = False):
        # Offline, the pool waits on AI topic checks rather than on the forum.
        super().__init__(name=self.__name, pool_size=self.__offline_pool_size if offline else 1)
        self.__ai_forum_verifier: Optional[AiForumVerifier] = ai_forum_verifier
        self.__lock: Lock = Lock()
        self.__stage_dir: Path = snapshot_dir.get_stage_dir() / "3-enricher" / "forum"
        self.__anki_forum_service: AnkiForumService = anki_forum_service
        self.__anki_forum_infos: dict[AddonId, Optional[AnkiForumInfo]] = {}

    def enrich(self, addon_infos: AddonInfos) -> AddonInfos:
        return AddonInfos([self.__enrich(addon_info, self.__anki_forum_infos[addon_info.header.id])
                           for addon_info in addon_infos])

    def _download(self, addon_info: AddonInfo) -> None:
        anki_forum: Optional[AnkiForumInfo] = self.__fetch(addon_info)
        with self.__lock:
            self.__anki_forum_infos[addon_info.header.id] = anki_forum

    def __fetch(self, addon_info: AddonInfo) -> Optional[AnkiForumInfo]:
        anki_forum_url: Optional[URL] = addon_info.forum.anki_forum_url if addon_info.forum else None
        if not anki_forum_url:
            return None
        topic_slug: Optional[TopicSlug] = AnkiForumTopic.extract_topic_slug(anki_forum_url)
        topic_id: Optional[TopicId] = AnkiForumTopic.extract_topic_id(anki_forum_url)
        topic_source: Optional[AnkiForumTopicSource] = addon_info.forum.topic_source
        if topic_source == AnkiForumTopicSource.MOST_LINKED:
            answer: Optional[AiForumAnswer] = self.__verify(addon_info, anki_forum_url, topic_slug, topic_id)
            if answer is not None and not answer.own:
                log.debug(f"Forum topic {anki_forum_url} rejected for addon {addon_info.header.id}")
                return None
            if answer is not None:
                topic_source = AnkiForumTopicSource.AI
        last_posted_at: Optional[LastPostedAt] = self.__anki_forum_service.get_last_posted_at(topic_slug, topic_id)
        posts_count: Optional[PostsCount] = self.__anki_forum_service.get_posts_count(topic_slug, topic_id)
        return AnkiForumInfo(anki_forum_url, topic_slug, topic_id, last_posted_at, posts_count, topic_source)

    def __verify(self, addon_info: AddonInfo, anki_forum_url: URL, topic_slug: Optional[TopicSlug],
                 topic_id: Optional[TopicId]) -> Optional[AiForumAnswer]:
        if self.__ai_forum_verifier is None:
            return None
        topic: Optional[AnkiForumTopicContent] = self.__anki_forum_service.get_topic_content(topic_slug, topic_id)
        if topic is None:
            return None
        try:
            return self.__ai_forum_verifier.verify(addon_info, anki_forum_url, topic)
        except Exception as e:
            raise RuntimeError(f"Cannot verify forum topic of addon: {addon_info.header.id}") from e

    def _done(self) -> int:
        with self.__lock:
            return len(self.__anki_forum_infos)

    def __enrich(self, addon_info: AddonInfo, anki_forum_info: Optional[AnkiForumInfo]) -> AddonInfo:
        enriched_addon_info: AddonInfo = copy.replace(addon_info, forum=anki_forum_info)
        addon_json_file: Path = self.__stage_dir / f"{addon_info.header.id}.json"
        JsonHelper.write_addon_info_to_file(addon_info, addon_json_file)
        log.info(f"Enriched ({self.__name}): {addon_info.header.id}")
        return enriched_addon_info
