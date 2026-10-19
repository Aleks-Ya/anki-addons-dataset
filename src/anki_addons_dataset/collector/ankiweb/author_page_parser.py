import re
from typing import Optional

from bs4 import BeautifulSoup, Tag

from anki_addons_dataset.common.data_types import AddonId, HtmlStr


class AuthorPageParser:
    __item_href: re.Pattern[str] = re.compile(r'^/shared/info/(\d+)$')

    @staticmethod
    def parse_author_page(html: HtmlStr) -> list[AddonId]:
        soup: BeautifulSoup = BeautifulSoup(html, 'html.parser')
        main: Optional[Tag] = soup.find("main")
        if main is None:
            return []
        item_ids: set[AddonId] = set()
        for anchor in main.find_all('a', href=AuthorPageParser.__item_href):
            match: Optional[re.Match[str]] = AuthorPageParser.__item_href.match(str(anchor['href']))
            if match:
                item_ids.add(AddonId(int(match.group(1))))
        return sorted(item_ids)
