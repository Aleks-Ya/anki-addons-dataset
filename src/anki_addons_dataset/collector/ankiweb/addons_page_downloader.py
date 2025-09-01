from pathlib import Path

from anki_addons_dataset.collector.ankiweb.addons_page_parser import AddonsPageParser
from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.common.data_types import AddonHeader, HtmlStr
from anki_addons_dataset.common.working_dir import VersionDir


class AddonsPageDownloader:
    def __init__(self, page_downloader: PageDownloader, version_dir: VersionDir, offline: bool) -> None:
        self.__page_downloader: PageDownloader = page_downloader
        self.__raw_dir: Path = version_dir.get_raw_dir() / "1-anki-web"
        self.__offline: bool = offline

    def get_headers(self) -> list[AddonHeader]:
        html: HtmlStr = self.__load_addons_page()
        addon_headers: list[AddonHeader] = AddonsPageParser.parse_addons_page(html)
        return addon_headers

    def __load_addons_page(self) -> HtmlStr:
        raw_file: Path = self.__raw_dir / "addons_page.html"
        if not raw_file.exists():
            print(f"Downloading addons page to {raw_file}")
            if self.__offline:
                raise RuntimeError("Offline mode is enabled")
            raw_file.parent.mkdir(parents=True, exist_ok=True)
            html: HtmlStr = self.__page_downloader.load_page("https://ankiweb.net/shared/addons")
            raw_file.write_text(html)
        print(f"Reading addons page from {raw_file}")
        return HtmlStr(raw_file.read_text())
