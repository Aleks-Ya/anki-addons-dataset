import copy
import logging
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AuthorInfo

log: Logger = logging.getLogger(__name__)


class AuthorResolver:
    def __init__(self, overrider: Overrider) -> None:
        self.__overrider: Overrider = overrider

    def resolve(self, addon_infos: AddonInfos,
                author_items: Optional[dict[AddonId, list[AddonId]]]) -> AddonInfos:
        if author_items is None:
            return addon_infos
        catalog: set[AddonId] = {addon_info.header.id for addon_info in addon_infos}
        parents: dict[AddonId, AddonId] = {addon_id: addon_id for addon_id in catalog}
        covered: set[AddonId] = set()
        for owner_id, item_ids in author_items.items():
            members: list[AddonId] = [item_id for item_id in [owner_id, *item_ids] if item_id in catalog]
            covered.update(members)
            for member in members[1:]:
                AuthorResolver.__union(parents, members[0], member)
        for addon_id in sorted(catalog):
            same_author_id: Optional[AddonId] = self.__overrider.override_same_author(addon_id)
            if same_author_id is not None and same_author_id in catalog:
                AuthorResolver.__union(parents, addon_id, same_author_id)
                covered.update([addon_id, same_author_id])
        groups: dict[AddonId, list[AddonId]] = {}
        for addon_id in sorted(catalog):
            groups.setdefault(AuthorResolver.__find(parents, addon_id), []).append(addon_id)
        resolved: list[AddonInfo] = []
        unresolved_count: int = 0
        for addon_info in addon_infos:
            addon_id: AddonId = addon_info.header.id
            group: list[AddonId] = groups[AuthorResolver.__find(parents, addon_id)]
            if addon_id in covered or not addon_info.page.other_items_count:
                author: Optional[AuthorInfo] = AuthorInfo(group[0], list(group))
            else:
                author = None
                unresolved_count += 1
            resolved.append(copy.replace(addon_info, author=author))
        if unresolved_count:
            log.warning(f"{unresolved_count} addons have other items, but no author page covers them")
        return AddonInfos(resolved)

    @staticmethod
    def __find(parents: dict[AddonId, AddonId], addon_id: AddonId) -> AddonId:
        root: AddonId = addon_id
        while parents[root] != root:
            root = parents[root]
        while parents[addon_id] != root:
            parents[addon_id], addon_id = root, parents[addon_id]
        return root

    @staticmethod
    def __union(parents: dict[AddonId, AddonId], first: AddonId, second: AddonId) -> None:
        first_root: AddonId = AuthorResolver.__find(parents, first)
        second_root: AddonId = AuthorResolver.__find(parents, second)
        parents[max(first_root, second_root)] = min(first_root, second_root)
