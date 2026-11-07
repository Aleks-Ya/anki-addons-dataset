from itertools import groupby
from typing import Optional

from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.collector.url_parser import UrlParser
from anki_addons_dataset.common.data_types import AddonInfo, AnkiForumTopicSource, PageLinkSection, URL


class AnkiForumTopicSelector:

    def __init__(self, overrider: Overrider):
        self.__overrider: Overrider = overrider

    def decided_topic(self, addon_info: AddonInfo) -> Optional[tuple[URL, AnkiForumTopicSource]]:
        override_url: Optional[URL] = self.__overrider.override_anki_forum_url(addon_info.header.id)
        if override_url:
            return override_url, AnkiForumTopicSource.OVERRIDE
        contact_author_url: Optional[URL] = addon_info.page.contact_author_url
        if contact_author_url is not None:
            contact_forum_urls: list[URL] = UrlParser.find_anki_forum_links([contact_author_url])
            if contact_forum_urls:
                return contact_forum_urls[0], AnkiForumTopicSource.CONTACT_AUTHOR
        description_urls: list[URL] = [link.url for link in addon_info.page.links
                                       if link.section == PageLinkSection.DESCRIPTION for _ in range(link.count)]
        urls_sorted: list[URL] = sorted(UrlParser.find_anki_forum_links(description_urls))
        counts: dict[URL, int] = {url: len(list(group)) for url, group in groupby(urls_sorted)}
        if len(counts) == 0:
            return None
        max_tuple: tuple[URL, int] = max(counts.items(), key=lambda item: item[1])
        return max_tuple[0], AnkiForumTopicSource.MOST_LINKED
