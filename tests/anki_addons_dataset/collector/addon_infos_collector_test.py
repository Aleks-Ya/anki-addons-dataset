from dataclasses import replace
from typing import Optional
from unittest.mock import Mock

import pytest

from anki_addons_dataset.collector.addon_infos_collector import AddonInfosCollector
from anki_addons_dataset.collector.author_resolver import AuthorResolver
from anki_addons_dataset.common.data_types import AddonHeader, AddonId, AddonInfo, AddonInfos


def __collector(headers: list[AddonHeader], addon_info: AddonInfo,
                max_addons: Optional[int]) -> tuple[AddonInfosCollector, Mock, Mock, Mock]:
    ankiweb_service: Mock = Mock()
    ankiweb_service.get_headers.return_value = headers
    ankiweb_service.get_addon_info.side_effect = lambda header: replace(addon_info, header=header)
    ankiweb_service.has_author_pages.return_value = False
    github_enricher: Mock = Mock()
    github_enricher.enrich.side_effect = lambda addon_infos: addon_infos
    anki_forum_enricher: Mock = Mock()
    anki_forum_enricher.enrich.side_effect = lambda addon_infos: addon_infos
    author_resolver: Mock = Mock(spec=AuthorResolver)
    author_resolver.resolve.side_effect = lambda addon_infos, author_items: addon_infos
    collector: AddonInfosCollector = AddonInfosCollector(
        ankiweb_service, github_enricher, anki_forum_enricher, author_resolver, max_addons)
    return collector, ankiweb_service, github_enricher, anki_forum_enricher


@pytest.fixture
def addon_headers(addon_header: AddonHeader) -> list[AddonHeader]:
    return [replace(addon_header, id=AddonId(addon_id)) for addon_id in [10, 20, 30, 40, 50]]


def test_collect_addons_without_a_sample(addon_headers: list[AddonHeader], addon_info: AddonInfo):
    collector, ankiweb_service, github_enricher, anki_forum_enricher = __collector(addon_headers, addon_info, None)

    addon_infos: AddonInfos = collector.collect_addons()

    assert [info.header.id for info in addon_infos] == [10, 20, 30, 40, 50]
    assert ankiweb_service.get_addon_info.call_count == 5
    assert github_enricher.download_in_background.call_count == 5
    assert anki_forum_enricher.download_in_background.call_count == 5


def test_collect_addons_keeps_the_first_addons_by_id(addon_headers: list[AddonHeader], addon_info: AddonInfo):
    collector, ankiweb_service, github_enricher, anki_forum_enricher = __collector(addon_headers, addon_info, 2)

    addon_infos: AddonInfos = collector.collect_addons()

    assert [info.header.id for info in addon_infos] == [10, 20]
    assert ankiweb_service.get_addon_info.call_count == 2
    assert github_enricher.download_in_background.call_count == 2
    assert anki_forum_enricher.download_in_background.call_count == 2


def test_collect_addons_with_a_sample_larger_than_the_catalog(addon_headers: list[AddonHeader],
                                                              addon_info: AddonInfo):
    collector, ankiweb_service, _, _ = __collector(addon_headers, addon_info, 99)

    assert len(collector.collect_addons()) == 5
    assert ankiweb_service.get_addon_info.call_count == 5


def test_collect_addons_downloads_one_author_page_per_author(addon_headers: list[AddonHeader], addon_info: AddonInfo):
    other_items_counts: dict[int, int] = {10: 1, 20: 1, 30: 0, 40: 1, 50: 1}
    collector, ankiweb_service, _, _ = __collector(addon_headers, addon_info, None)
    ankiweb_service.get_addon_info.side_effect = lambda header: replace(
        addon_info, header=header, page=replace(addon_info.page, other_items_count=other_items_counts[header.id]))
    ankiweb_service.has_author_pages.return_value = True
    ankiweb_service.get_author_item_ids.side_effect = lambda addon_id: {
        10: [AddonId(10), AddonId(20)], 40: None, 50: [AddonId(40), AddonId(50)]}[addon_id]

    collector.collect_addons()

    assert [call.args[0] for call in ankiweb_service.get_author_item_ids.call_args_list] == [10, 40, 50]
