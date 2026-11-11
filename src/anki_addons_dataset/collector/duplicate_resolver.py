import copy
import logging
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.overrider.overrider import DuplicateOverride, Overrider
from anki_addons_dataset.collector.package.package_cache_index import PackageKey
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AddonPackage, DuplicateEvidence, \
    DuplicateRelation

log: Logger = logging.getLogger(__name__)


class DuplicateResolver:
    def __init__(self, overrider: Overrider) -> None:
        self.__overrider: Overrider = overrider

    def resolve(self, addon_infos: AddonInfos) -> AddonInfos:
        catalog: set[AddonId] = {addon_info.header.id for addon_info in addon_infos}
        originals: dict[AddonId, AddonId] = DuplicateResolver.__originals(addon_infos)
        resolved: list[AddonInfo] = []
        for addon_info in addon_infos:
            override: Optional[DuplicateOverride] = self.__overrider.override_duplicate_of(addon_info.header.id)
            duplicate_of: Optional[DuplicateRelation] = None
            if override is not None:
                if override.original is not None and override.original in catalog \
                        and override.original != addon_info.header.id:
                    duplicate_of = DuplicateRelation(override.original, DuplicateEvidence.OVERRIDE)
            elif addon_info.header.id in originals:
                duplicate_of = DuplicateRelation(originals[addon_info.header.id], DuplicateEvidence.SAME_PACKAGE)
            resolved.append(copy.replace(addon_info, duplicate_of=duplicate_of))
        log.info(f"Addons with a duplicate_of: "
                 f"{sum(1 for addon_info in resolved if addon_info.duplicate_of is not None)}")
        return AddonInfos(resolved)

    @staticmethod
    def __originals(addon_infos: AddonInfos) -> dict[AddonId, AddonId]:
        groups: dict[str, list[tuple[AddonInfo, AddonPackage]]] = {}
        for addon_info in addon_infos:
            package: Optional[AddonPackage] = DuplicateResolver.__newest_package(addon_info)
            content_hash: Optional[str] = PackageKey.content_hash(package.file_name) if package else None
            if package is not None and content_hash is not None:
                groups.setdefault(content_hash, []).append((addon_info, package))
        originals: dict[AddonId, AddonId] = {}
        for members in groups.values():
            if len(members) < 2:
                continue
            original: AddonId = min(members, key=lambda member: (
                -member[0].header.rating, member[1].updated, member[0].header.id))[0].header.id
            for addon_info, _ in members:
                if addon_info.header.id != original:
                    originals[addon_info.header.id] = original
        return originals

    @staticmethod
    def __newest_package(addon_info: AddonInfo) -> Optional[AddonPackage]:
        return addon_info.package.branches[-1] if addon_info.package and addon_info.package.branches else None
