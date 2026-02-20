import logging
from logging import Logger

from anki_addons_dataset.collector.ankiforum.ankiforum_enricher import AnkiForumEnricher
from anki_addons_dataset.collector.github.github_enricher import GithubEnricher
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonInfos
from anki_addons_dataset.collector.ankiweb.ankiweb_service import AnkiWebService

log: Logger = logging.getLogger(__name__)


class AddonCollector:
    def __init__(self, ankiweb_service: AnkiWebService, github_enricher: GithubEnricher,
                 anki_forum_enricher: AnkiForumEnricher, overrider: Overrider):
        self.__ankiweb_service: AnkiWebService = ankiweb_service
        self.__github_enricher: GithubEnricher = github_enricher
        self.__anki_forum_enricher: AnkiForumEnricher = anki_forum_enricher
        self.__overrider: Overrider = overrider

    def collect_addons(self) -> AddonInfos:
        self.__github_enricher.start()
        self.__anki_forum_enricher.start()

        addon_headers: list[AddonHeader] = self.__ankiweb_service.get_headers()
        log.info(f"Addon number: {len(addon_headers)}")
        addons_infos: AddonInfos = self.__get_addon_infos(addon_headers)
        log.info("All addons are added to queue")
        self.__github_enricher.wait_download_finish()
        self.__anki_forum_enricher.wait_download_finish()
        github_enriched_addon_infos: AddonInfos = self.__github_enricher.enrich(addons_infos)
        anki_forum_enriched_addon_infos: AddonInfos = self.__anki_forum_enricher.enrich(github_enriched_addon_infos)
        log.info("All addons are enriched")

        overridden_addon_infos: AddonInfos = self.__overrider.override(anki_forum_enriched_addon_infos)
        return overridden_addon_infos

    def __get_addon_infos(self, addon_headers: list[AddonHeader]) -> AddonInfos:
        addon_infos: list[AddonInfo] = []
        for i, addon_header in enumerate(addon_headers):
            log.info(f"Parsing addon page: {addon_header.id} ({i}/{len(addon_headers)})")
            addon_info: AddonInfo = self.__ankiweb_service.get_addon_info(addon_header)
            self.__github_enricher.download_in_background(addon_info)
            self.__anki_forum_enricher.download_in_background(addon_info)
            addon_infos.append(addon_info)
        return AddonInfos(addon_infos)
