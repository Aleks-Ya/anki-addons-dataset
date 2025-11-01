from pathlib import Path
import logging
from logging import Logger

from anki_addons_dataset.collector.ankiweb.addon_page_parser import AddonPageParser
from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonHeader, HtmlStr
from anki_addons_dataset.common.json_helper import JsonHelper
from anki_addons_dataset.common.working_dir import VersionDir

log: Logger = logging.getLogger(__name__)


class AddonPageDownloader:
    def __init__(self, page_downloader: PageDownloader, version_dir: VersionDir, addon_page_parser: AddonPageParser,
                 offline: bool) -> None:
        self.__addon_page_parser: AddonPageParser = addon_page_parser
        self.__page_downloader: PageDownloader = page_downloader
        self.__raw_dir: Path = version_dir.get_raw_dir() / "1-anki-web"
        self.__stage_dir: Path = version_dir.get_stage_dir() / "1-anki-web"
        self.__offline: bool = offline

    def get_addon_info(self, addon_header: AddonHeader) -> AddonInfo:
        html: HtmlStr = self.__load_addon_page(addon_header.id)
        addon_info: AddonInfo = self.__addon_page_parser.parse_addon_page(addon_header, html)
        addon_json_file: Path = self.__stage_dir / "addon" / f"{addon_header.id}.json"
        JsonHelper.write_addon_info_to_file(addon_info, addon_json_file)
        return addon_info

    def __load_addon_page(self, addon_id: AddonId) -> HtmlStr:
        raw_file: Path = self.__raw_dir / "addon" / f"{addon_id}.html"
        if raw_file.exists() and raw_file.stat().st_size == 0:
            raw_file.unlink()
            log.info(f"Removed empty file: {raw_file}")
        if not raw_file.exists():
            log.info(f"Downloading addon page to {raw_file}")
            if self.__offline:
                raise RuntimeError("Offline mode is enabled")
            raw_file.parent.mkdir(parents=True, exist_ok=True)
            html: HtmlStr = self.__page_downloader.load_page(f"https://ankiweb.net/shared/info/{addon_id}")
            raw_file.write_text(html)
        return HtmlStr(raw_file.read_text())
