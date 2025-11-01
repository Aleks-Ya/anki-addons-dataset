from pathlib import Path
from unittest.mock import Mock

from anki_addons_dataset.collector.ankiweb.addon_page_downloader import AddonPageDownloader
from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.common.data_types import AddonInfo, HtmlStr, AddonHeader, AddonId
from anki_addons_dataset.common.working_dir import VersionDir


# Re-download cached files that are empty
def test_download_empty_files(addon_page_downloader: AddonPageDownloader, page_downloader: PageDownloader,
                              version_dir: VersionDir):
    addon_html_file: Path = Path(__file__).parent / "1188705668.html"
    addon_html: HtmlStr = HtmlStr(addon_html_file.read_text())
    page_downloader.load_page = Mock(return_value=addon_html)

    addon_id: AddonId = AddonId(1188705668)
    addon_file: Path = version_dir.get_raw_dir() / "1-anki-web" / "addon" / f"{addon_id}.html"
    addon_file.parent.mkdir(parents=True, exist_ok=True)
    addon_file.write_text("")

    addon_header: AddonHeader = AddonHeader(
        id=addon_id,
        name="Note Size - sort notes by size and see collection size",
        addon_page="https://ankiweb.net/shared/info/1188705668",
        rating=12,
        update_date="2025-04-19",
        versions="24.04.1-25.02.1+ (Updated 2025-04-19) ")
    addon_info: AddonInfo = addon_page_downloader.get_addon_info(addon_header)
    assert addon_info.page.anki_forum_url == 'https://forums.ankiweb.net/t/note-size-addon-support/46001'
