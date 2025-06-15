from anki_addons_dataset.collector.enricher.enricher import Enricher
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonInfo
from anki_addons_dataset.collector.ankiweb.ankiweb_service import AnkiWebService


class AddonCollector:
    def __init__(self, ankiweb_service: AnkiWebService, enricher: Enricher, overrider: Overrider):
        self.__ankiweb_service: AnkiWebService = ankiweb_service
        self.__enricher: Enricher = enricher
        self.__overrider: Overrider = overrider

    def collect_addons(self) -> list[AddonInfo]:
        addon_infos: list[AddonInfo] = self.__ankiweb_service.load_addon_infos()
        enriched_addon_infos: list[AddonInfo] = self.__enricher.enrich_list(addon_infos)
        overridden_addon_infos: list[AddonInfo] = self.__overrider.override(enriched_addon_infos)
        return overridden_addon_infos
