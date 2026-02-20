from pathlib import Path
from typing import Optional
import logging
from logging import Logger

from anki_addons_dataset.collector.ankiforum.ankiforum_service import AnkiForumService
from anki_addons_dataset.collector.enricher import Enricher
from anki_addons_dataset.common.data_types import AddonInfo, AddonId, \
    AnkiForumInfo, TopicSlug, TopicId, LastPostedAt, AddonInfos
from anki_addons_dataset.common.json_helper import JsonHelper
from anki_addons_dataset.common.working_dir import VersionDir

log: Logger = logging.getLogger(__name__)


class AnkiForumEnricher(Enricher):
    __name: str = "AnkiForum"

    def __init__(self, version_dir: VersionDir, anki_forum_service: AnkiForumService):
        super().__init__(name=self.__name)
        self.__stage_dir: Path = version_dir.get_stage_dir() / "3-enricher" / "forum"
        self.__anki_forum_service: AnkiForumService = anki_forum_service
        self.__anki_forum_infos: dict[AddonId, AnkiForumInfo] = {}

    def enrich(self, addon_infos: AddonInfos) -> AddonInfos:
        return AddonInfos([self.__enrich(addon_info, self.__anki_forum_infos[addon_info.header.id])
                           for addon_info in addon_infos])

    def _download(self, addon_info: AddonInfo) -> None:
        if addon_info.page.anki_forum_url:
            topic_slug: TopicSlug = self.__anki_forum_service.extract_topic_slug(addon_info.page.anki_forum_url)
            topic_id: TopicId = self.__anki_forum_service.extract_topic_id(addon_info.page.anki_forum_url)
            last_posted_at: Optional[LastPostedAt] = self.__anki_forum_service.get_last_posted_at(topic_slug, topic_id)
            anki_forum: Optional[AnkiForumInfo] = AnkiForumInfo(topic_slug, topic_id, last_posted_at)
        else:
            anki_forum: Optional[AnkiForumInfo] = None
        self.__anki_forum_infos[addon_info.header.id] = anki_forum

    def _done(self) -> int:
        return len(self.__anki_forum_infos)

    def __enrich(self, addon_info: AddonInfo, anki_forum_info: AnkiForumInfo) -> AddonInfo:
        enriched_addon_info: AddonInfo = AddonInfo(
            addon_info.header, addon_info.page, addon_info.github, anki_forum_info)
        addon_json_file: Path = self.__stage_dir / f"{addon_info.header.id}.json"
        JsonHelper.write_addon_info_to_file(addon_info, addon_json_file)
        log.info(f"Enriched: {addon_info.header.id}")
        return enriched_addon_info
