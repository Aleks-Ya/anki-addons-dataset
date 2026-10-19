import logging
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.ankiforum.ankiforum_enricher import AnkiForumEnricher
from anki_addons_dataset.collector.ankiweb.ankiweb_service import AnkiWebService
from anki_addons_dataset.collector.author_resolver import AuthorResolver
from anki_addons_dataset.collector.github.github_enricher import GithubEnricher
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonInfos, AddonId

log: Logger = logging.getLogger(__name__)


class AddonInfosCollector:
    def __init__(self, ankiweb_service: AnkiWebService, github_enricher: GithubEnricher,
                 anki_forum_enricher: AnkiForumEnricher, author_resolver: AuthorResolver,
                 max_addons: Optional[int] = None):
        self.__ankiweb_service: AnkiWebService = ankiweb_service
        self.__author_resolver: AuthorResolver = author_resolver
        self.__github_enricher: GithubEnricher = github_enricher
        self.__anki_forum_enricher: AnkiForumEnricher = anki_forum_enricher
        self.__max_addons: Optional[int] = max_addons

    def collect_addons(self) -> AddonInfos:
        self.__github_enricher.start()
        self.__anki_forum_enricher.start()

        addon_headers: list[AddonHeader] = self.__ankiweb_service.get_headers()
        log.info(f"Addon number: {len(addon_headers)}")
        if self.__max_addons is not None:
            addon_headers = addon_headers[:self.__max_addons]
            log.info(f"Addon sample: processing the first {len(addon_headers)} addons by id")
        addons_infos: AddonInfos = self.__get_addon_infos(addon_headers)
        log.info("All addons are added to queue")
        author_items: Optional[dict[AddonId, list[AddonId]]] = self.__get_author_items(addons_infos)
        self.__github_enricher.wait_download_finish()
        self.__anki_forum_enricher.wait_download_finish()
        github_enriched_addon_infos: AddonInfos = self.__github_enricher.enrich(addons_infos)
        anki_forum_enriched_addon_infos: AddonInfos = self.__anki_forum_enricher.enrich(github_enriched_addon_infos)
        log.info("All addons are enriched")
        return self.__author_resolver.resolve(anki_forum_enriched_addon_infos, author_items)

    def __get_addon_infos(self, addon_headers: list[AddonHeader]) -> AddonInfos:
        addon_infos: list[AddonInfo] = []
        for i, addon_header in enumerate(addon_headers):
            log.info(f"Parsing addon page: {addon_header.id} ({i}/{len(addon_headers)})")
            addon_info: AddonInfo = self.__ankiweb_service.get_addon_info(addon_header)
            self.__github_enricher.download_in_background(addon_info)
            self.__anki_forum_enricher.download_in_background(addon_info)
            addon_infos.append(addon_info)
        return AddonInfos(addon_infos)

    def __get_author_items(self, addon_infos: AddonInfos) -> Optional[dict[AddonId, list[AddonId]]]:
        if not self.__ankiweb_service.has_author_pages():
            log.info("No author pages in the snapshot")
            return None
        author_items: dict[AddonId, list[AddonId]] = {}
        covered: set[AddonId] = set()
        for addon_info in addon_infos:
            addon_id: AddonId = addon_info.header.id
            if not addon_info.page.other_items_count or addon_id in covered:
                continue
            log.info(f"Parsing author page: {addon_id}")
            item_ids: Optional[list[AddonId]] = self.__ankiweb_service.get_author_item_ids(addon_id)
            if item_ids is not None:
                author_items[addon_id] = item_ids
                covered.update(item_ids)
        log.info(f"Author pages: {len(author_items)}")
        return author_items
