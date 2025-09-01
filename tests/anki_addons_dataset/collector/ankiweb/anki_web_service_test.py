from pathlib import Path
from unittest.mock import Mock

from anki_addons_dataset.collector.ankiweb.ankiweb_service import AnkiWebService
from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.common.data_types import AddonInfo, HtmlStr


def test_load_addon_infos(ankiweb_service: AnkiWebService, page_downloader: PageDownloader):
    addons_html_file: Path = Path(__file__).parent / "addons_page.html"
    addons_html: HtmlStr = HtmlStr(addons_html_file.read_text())
    addon_html_file: Path = Path(__file__).parent / "1188705668.html"
    addon_html: HtmlStr = HtmlStr(addon_html_file.read_text())
    addons_number: int = 2066
    htmls: list[HtmlStr] = [addons_html] + [addon_html] * addons_number
    page_downloader.load_page = Mock(side_effect=htmls)
    addon_infos: list[AddonInfo] = ankiweb_service.load_addon_infos()
    print(addon_infos)
