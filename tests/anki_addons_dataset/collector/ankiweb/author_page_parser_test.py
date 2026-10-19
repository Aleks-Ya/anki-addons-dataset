from pathlib import Path

from anki_addons_dataset.collector.ankiweb.author_page_parser import AuthorPageParser
from anki_addons_dataset.common.data_types import AddonId, HtmlStr


def test_parse_author_page():
    html: HtmlStr = HtmlStr((Path(__file__).parent / "by_author_394069868.html").read_text())
    assert AuthorPageParser.parse_author_page(html) == [
        AddonId(394069868), AddonId(1199786235), AddonId(1269480121), AddonId(1287298831)]


def test_parse_author_page_ignores_links_outside_main():
    html: HtmlStr = HtmlStr('<html><body><nav><a href="/shared/info/7">Nav</a></nav>'
                            '<main><ul><li><a href="/shared/info/5">Item</a></li>'
                            '<li><a href="/shared/info/5">Duplicate</a></li>'
                            '<li><a href="/shared/review/6">Review</a></li></ul></main></body></html>')
    assert AuthorPageParser.parse_author_page(html) == [AddonId(5)]


def test_parse_author_page_without_main():
    assert AuthorPageParser.parse_author_page(HtmlStr("<html><body></body></html>")) == []
