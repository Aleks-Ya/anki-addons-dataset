from pathlib import Path
import logging
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.ankiweb.author_page_parser import AuthorPageParser
from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.common.data_types import AddonId, HtmlStr
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


class AuthorPageDownloader:
    __item_xpath: str = "/html/body/div/main//ul/li/a"

    def __init__(self, page_downloader: PageDownloader, snapshot_dir: SnapshotDir, offline: bool) -> None:
        self.__page_downloader: PageDownloader = page_downloader
        self.__raw_dir: Path = snapshot_dir.get_raw_dir() / "1-anki-web" / "by-author"
        self.__offline: bool = offline
        if not offline:
            self.__raw_dir.mkdir(parents=True, exist_ok=True)

    def has_author_pages(self) -> bool:
        return self.__raw_dir.is_dir()

    def get_author_item_ids(self, addon_id: AddonId) -> Optional[list[AddonId]]:
        html: Optional[HtmlStr] = self.__load_author_page(addon_id)
        return AuthorPageParser.parse_author_page(html) if html is not None else None

    def __load_author_page(self, addon_id: AddonId) -> Optional[HtmlStr]:
        raw_file: Path = self.__raw_dir / f"{addon_id}.html"
        if raw_file.exists() and raw_file.stat().st_size == 0:
            raw_file.unlink()
            log.info(f"Removed empty file: {raw_file}")
        if not raw_file.exists():
            if self.__offline:
                return None
            log.debug(f"Downloading author page to {raw_file}")
            try:
                html: HtmlStr = self.__page_downloader.load_page(
                    f"https://ankiweb.net/shared/by-author/{addon_id}", self.__item_xpath)
            except Exception as e:
                log.warning(f"Cannot download author page: {addon_id}: {e}")
                return None
            raw_file.write_text(html)
        return HtmlStr(raw_file.read_text())
