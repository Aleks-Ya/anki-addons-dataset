from anki_addons_dataset.collector.ankiweb.addon_page_downloader import AddonPageDownloader
from anki_addons_dataset.collector.ankiweb.addons_page_downloader import AddonsPageDownloader
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader


class AnkiWebService:
    def __init__(self, addons_page_downloader: AddonsPageDownloader,
                 addon_page_downloader: AddonPageDownloader) -> None:
        self.__addons_page_downloader: AddonsPageDownloader = addons_page_downloader
        self.__addon_page_downloader: AddonPageDownloader = addon_page_downloader

    def get_headers(self) -> list[AddonHeader]:
        return self.__addons_page_downloader.get_headers()

    def get_addon_info(self, addon_header: AddonHeader) -> AddonInfo:
        return self.__addon_page_downloader.get_addon_info(addon_header)
