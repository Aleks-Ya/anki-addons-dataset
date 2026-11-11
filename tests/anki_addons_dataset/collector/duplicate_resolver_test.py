from dataclasses import replace
from datetime import date
from typing import Optional
from unittest.mock import Mock

from anki_addons_dataset.collector.duplicate_resolver import DuplicateResolver
from anki_addons_dataset.collector.overrider.overrider import DuplicateOverride, Overrider
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AddonPackage, AddonPackages, \
    AddonRating, AnkiPointVersion, DuplicateEvidence, DuplicateRelation


def __package(content_hash: str, min_point_version: int = 45, updated: date = date(2026, 1, 1)) -> AddonPackage:
    return AddonPackage(f"{min_point_version}-{updated.isoformat()}-{content_hash}.ankiaddon",
                        AnkiPointVersion(min_point_version), updated, 100, None, None, 1, 100, 1, 10, [], {})


def __addon(addon_info: AddonInfo, addon_id: int, packages: Optional[list[AddonPackage]],
            rating: int = 0) -> AddonInfo:
    return replace(addon_info, header=replace(addon_info.header, id=AddonId(addon_id), rating=AddonRating(rating)),
                   package=AddonPackages(packages) if packages is not None else None)


def __resolve(addon_infos: list[AddonInfo],
              duplicate_of: Optional[dict[int, Optional[int]]] = None) -> dict[int, Optional[DuplicateRelation]]:
    overrider: Mock = Mock(spec=Overrider)
    overrides: dict[int, Optional[int]] = duplicate_of or {}
    overrider.override_duplicate_of.side_effect = lambda addon_id: DuplicateOverride(
        AddonId(overrides[addon_id]) if overrides[addon_id] is not None else None) \
        if addon_id in overrides else None
    resolved: AddonInfos = DuplicateResolver(overrider).resolve(AddonInfos(addon_infos))
    return {addon_info.header.id: addon_info.duplicate_of for addon_info in resolved}


def __same_package(addon_id: int) -> DuplicateRelation:
    return DuplicateRelation(AddonId(addon_id), DuplicateEvidence.SAME_PACKAGE)


def test_the_best_rated_addon_is_the_original(addon_info: AddonInfo):
    assert __resolve([
        __addon(addon_info, 10, [__package("aaaaaaaaaaaa")], rating=3),
        __addon(addon_info, 20, [__package("aaaaaaaaaaaa")], rating=7),
        __addon(addon_info, 30, [__package("aaaaaaaaaaaa")], rating=1),
        __addon(addon_info, 40, [__package("bbbbbbbbbbbb")], rating=9)]) == {
        10: __same_package(20), 20: None, 30: __same_package(20), 40: None}


def test_a_tied_rating_goes_to_the_first_upload_then_the_lowest_id(addon_info: AddonInfo):
    assert __resolve([
        __addon(addon_info, 10, [__package("aaaaaaaaaaaa", updated=date(2026, 3, 1))]),
        __addon(addon_info, 20, [__package("aaaaaaaaaaaa", updated=date(2026, 2, 1))]),
        __addon(addon_info, 30, [__package("aaaaaaaaaaaa", updated=date(2026, 2, 1))])]) == {
        10: __same_package(20), 20: None, 30: __same_package(20)}


def test_only_the_highest_min_point_version_branch_counts(addon_info: AddonInfo):
    assert __resolve([
        __addon(addon_info, 10, [__package("aaaaaaaaaaaa", 1), __package("bbbbbbbbbbbb", 45)]),
        __addon(addon_info, 20, [__package("aaaaaaaaaaaa", 1), __package("cccccccccccc", 45)])]) == {
        10: None, 20: None}


def test_an_addon_without_a_package_is_ignored(addon_info: AddonInfo):
    assert __resolve([
        __addon(addon_info, 10, [__package("aaaaaaaaaaaa")]),
        __addon(addon_info, 20, None)]) == {10: None, 20: None}


def test_overrides_set_and_suppress_the_original(addon_info: AddonInfo):
    assert __resolve([
        __addon(addon_info, 10, [__package("aaaaaaaaaaaa")], rating=5),
        __addon(addon_info, 20, [__package("aaaaaaaaaaaa")]),
        __addon(addon_info, 30, None),
        __addon(addon_info, 40, None)], duplicate_of={20: None, 30: 10, 40: 99}) == {
        10: None, 20: None, 30: DuplicateRelation(AddonId(10), DuplicateEvidence.OVERRIDE), 40: None}
