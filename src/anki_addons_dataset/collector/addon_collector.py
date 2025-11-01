import logging
from logging import Logger

from anki_addons_dataset.collector.enricher.enricher import Enricher
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader
from anki_addons_dataset.collector.ankiweb.ankiweb_service import AnkiWebService

log: Logger = logging.getLogger(__name__)


class AddonCollector:
    def __init__(self, ankiweb_service: AnkiWebService, enricher: Enricher, overrider: Overrider):
        self.__ankiweb_service: AnkiWebService = ankiweb_service
        self.__enricher: Enricher = enricher
        self.__overrider: Overrider = overrider

    def collect_addons(self) -> list[AddonInfo]:
        addon_headers: list[AddonHeader] = self.__ankiweb_service.get_headers()
        addon_infos: list[AddonInfo] = []
        for i, addon_header in enumerate(addon_headers):
            log.info(f"Parsing addon page: {addon_header.id} ({i}/{len(addon_headers)})")
            addon_info: AddonInfo = self.__ankiweb_service.get_addon_info(addon_header)
            addon_infos.append(addon_info)
        log.info(f"Addon number: {len(addon_infos)}")

        enriched_addon_infos: list[AddonInfo] = self.__enricher.enrich_list(addon_infos)
        overridden_addon_infos: list[AddonInfo] = self.__overrider.override(enriched_addon_infos)
        return overridden_addon_infos
