from dataclasses import replace
from typing import Optional
from unittest.mock import Mock

from anki_addons_dataset.collector.author_resolver import AuthorResolver
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AuthorInfo


def __addon_infos(addon_info: AddonInfo, other_items_counts: dict[int, int]) -> AddonInfos:
    return AddonInfos([replace(addon_info, header=replace(addon_info.header, id=AddonId(addon_id)),
                               page=replace(addon_info.page, other_items_count=count), author=None)
                       for addon_id, count in other_items_counts.items()])


def __resolver(same_author: Optional[dict[int, int]] = None) -> AuthorResolver:
    overrider: Mock = Mock(spec=Overrider)
    overrider.override_same_author.side_effect = lambda addon_id: (same_author or {}).get(addon_id)
    return AuthorResolver(overrider)


def __authors(addon_infos: AddonInfos) -> dict[int, Optional[AuthorInfo]]:
    return {addon_info.header.id: addon_info.author for addon_info in addon_infos}


def __ids(*addon_ids: int) -> list[AddonId]:
    return [AddonId(addon_id) for addon_id in addon_ids]


def test_groups_chained_pages_under_the_smallest_id(addon_info: AddonInfo):
    addon_infos: AddonInfos = __addon_infos(addon_info, {30: 2, 10: 1, 20: 2, 40: 0})
    author_items: dict[AddonId, list[AddonId]] = {AddonId(30): __ids(20, 30), AddonId(20): __ids(10, 20)}

    authors: dict[int, Optional[AuthorInfo]] = __authors(__resolver().resolve(addon_infos, author_items))

    group: AuthorInfo = AuthorInfo(AddonId(10), __ids(10, 20, 30))
    assert authors == {30: group, 10: group, 20: group, 40: AuthorInfo(AddonId(40), __ids(40))}


def test_ignores_items_outside_the_catalog(addon_info: AddonInfo):
    addon_infos: AddonInfos = __addon_infos(addon_info, {20: 2})
    author_items: dict[AddonId, list[AddonId]] = {AddonId(20): __ids(5, 20, 99)}

    authors: dict[int, Optional[AuthorInfo]] = __authors(__resolver().resolve(addon_infos, author_items))

    assert authors == {20: AuthorInfo(AddonId(20), __ids(20))}


def test_an_uncovered_addon_with_other_items_is_unknown(addon_info: AddonInfo):
    addon_infos: AddonInfos = __addon_infos(addon_info, {10: 1, 20: 1})

    authors: dict[int, Optional[AuthorInfo]] = __authors(__resolver().resolve(addon_infos, {}))

    assert authors == {10: None, 20: None}


def test_a_snapshot_without_author_pages_has_no_authors(addon_info: AddonInfo):
    addon_infos: AddonInfos = __addon_infos(addon_info, {10: 0, 20: 3})

    authors: dict[int, Optional[AuthorInfo]] = __authors(__resolver().resolve(addon_infos, None))

    assert authors == {10: None, 20: None}


def test_the_same_author_override_merges_groups(addon_info: AddonInfo):
    addon_infos: AddonInfos = __addon_infos(addon_info, {10: 0, 20: 0, 30: 0})

    authors: dict[int, Optional[AuthorInfo]] = __authors(__resolver({30: 20}).resolve(addon_infos, {}))

    group: AuthorInfo = AuthorInfo(AddonId(20), __ids(20, 30))
    assert authors == {10: AuthorInfo(AddonId(10), __ids(10)), 20: group, 30: group}
