from typing import Optional

from anki_addons_dataset.collector.ankiweb.addon_page_downloader import AddonPageDownloader
from anki_addons_dataset.collector.ankiweb.addons_page_downloader import AddonsPageDownloader
from anki_addons_dataset.collector.ankiweb.author_page_downloader import AuthorPageDownloader
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId


class AnkiWebService:
    def __init__(self, addons_page_downloader: AddonsPageDownloader,
                 addon_page_downloader: AddonPageDownloader, author_page_downloader: AuthorPageDownloader) -> None:
        self.__addons_page_downloader: AddonsPageDownloader = addons_page_downloader
        self.__addon_page_downloader: AddonPageDownloader = addon_page_downloader
        self.__author_page_downloader: AuthorPageDownloader = author_page_downloader

    def get_headers(self) -> list[AddonHeader]:
        return self.__addons_page_downloader.get_headers()

    def get_addon_info(self, addon_header: AddonHeader) -> AddonInfo:
        return self.__addon_page_downloader.get_addon_info(addon_header)

    def has_author_pages(self) -> bool:
        return self.__author_page_downloader.has_author_pages()

    def get_author_item_ids(self, addon_id: AddonId) -> Optional[list[AddonId]]:
        return self.__author_page_downloader.get_author_item_ids(addon_id)
