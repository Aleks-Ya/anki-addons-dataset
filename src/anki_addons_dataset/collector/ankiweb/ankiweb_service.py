import logging
from logging import Logger

from anki_addons_dataset.collector.ankiweb.addon_page_downloader import AddonPageDownloader
from anki_addons_dataset.collector.ankiweb.addons_page_downloader import AddonsPageDownloader
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader

log: Logger = logging.getLogger(__name__)


class AnkiWebService:
    def __init__(self, addons_page_downloader: AddonsPageDownloader,
                 addon_page_downloader: AddonPageDownloader) -> None:
        self.__addons_page_downloader: AddonsPageDownloader = addons_page_downloader
        self.__addon_page_downloader: AddonPageDownloader = addon_page_downloader

    def load_addon_infos(self) -> list[AddonInfo]:
        addon_headers: list[AddonHeader] = self.__addons_page_downloader.get_headers()
        addon_infos: list[AddonInfo] = self.__addon_page_downloader.get_addon_infos(addon_headers)
        log.info(f"Addon number: {len(addon_infos)}")
        return addon_infos
