from pathlib import Path
from unittest.mock import Mock
import logging
from logging import Logger

from anki_addons_dataset.collector.ankiweb.ankiweb_service import AnkiWebService
from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.common.data_types import AddonInfo, HtmlStr, AddonHeader

log: Logger = logging.getLogger(__name__)


def test_load_addon_infos(ankiweb_service: AnkiWebService, page_downloader: PageDownloader):
    addons_html_file: Path = Path(__file__).parent / "addons_page.html"
    addons_html: HtmlStr = HtmlStr(addons_html_file.read_text())
    addon_html_file: Path = Path(__file__).parent / "1188705668.html"
    addon_html: HtmlStr = HtmlStr(addon_html_file.read_text())
    addons_number: int = 2066
    htmls: list[HtmlStr] = [addons_html] + [addon_html] * addons_number
    page_downloader.load_page = Mock(side_effect=htmls)
    addon_headers: list[AddonHeader] = ankiweb_service.get_headers()
    assert len(addon_headers) == addons_number
    for addon_header in addon_headers:
        addon_info: AddonInfo = ankiweb_service.get_addon_info(addon_header)
        log.info(addon_info)
