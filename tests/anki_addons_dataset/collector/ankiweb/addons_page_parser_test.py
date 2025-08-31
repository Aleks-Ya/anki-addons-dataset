from pathlib import Path

from anki_addons_dataset.collector.ankiweb.addons_page_parser import AddonsPageParser
from anki_addons_dataset.common.data_types import AddonHeader, AddonId


def test_addons_number():
    addons_html_file: Path = Path(__file__).parent / "addons_page.html"
    addons_html: str = addons_html_file.read_text()
    addon_headers: list[AddonHeader] = AddonsPageParser.parse_addons_page(addons_html)
    assert len(addon_headers) == 2066


def test_addons_order():
    addons_html_file: Path = Path(__file__).parent / "addons_page.html"
    addons_html: str = addons_html_file.read_text()
    addon_headers: list[AddonHeader] = AddonsPageParser.parse_addons_page(addons_html)
    addon_ids: list[AddonId] = [addon_header.id for addon_header in addon_headers]
    sorted_addon_ids: list[AddonId] = sorted(addon_ids)
    assert addon_ids == sorted_addon_ids
