import copy
import logging
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.overrider.overrider import Overrider, ForkOverride
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, ForkEvidence, ForkRelation, \
    GithubRepoId

log: Logger = logging.getLogger(__name__)


class ForkResolver:
    def __init__(self, overrider: Overrider) -> None:
        self.__overrider: Overrider = overrider

    def resolve(self, addon_infos: AddonInfos) -> AddonInfos:
        catalog: set[AddonId] = {addon_info.header.id for addon_info in addon_infos}
        repo_addons: dict[GithubRepoId, list[AddonId]] = {}
        for addon_info in addon_infos:
            repo_id: Optional[GithubRepoId] = ForkResolver.__own_repo_id(addon_info)
            if repo_id is not None:
                repo_addons.setdefault(repo_id, []).append(addon_info.header.id)
        resolved: list[AddonInfo] = []
        for addon_info in addon_infos:
            override: Optional[ForkOverride] = self.__overrider.override_fork_of(addon_info.header.id)
            forked_from: Optional[ForkRelation] = None
            if override is not None:
                if override.parent is not None and override.parent in catalog and override.parent != addon_info.header.id:
                    forked_from = ForkRelation(override.parent, ForkEvidence.OVERRIDE)
            else:
                forked_from = ForkResolver.__detect(addon_info, repo_addons)
            resolved.append(copy.replace(addon_info, forked_from=forked_from))
        log.info(f"Addons with a detected parent: "
                 f"{sum(1 for addon_info in resolved if addon_info.forked_from is not None)}")
        return AddonInfos(resolved)

    @staticmethod
    def __detect(addon_info: AddonInfo, repo_addons: dict[GithubRepoId, list[AddonId]]) -> Optional[ForkRelation]:
        addon_id: AddonId = addon_info.header.id
        ai_parent: Optional[AddonId] = addon_info.ai.fork_of if addon_info.ai else None
        if ai_parent == addon_id:
            ai_parent = None
        own_repo_id: Optional[GithubRepoId] = ForkResolver.__own_repo_id(addon_info)
        if addon_info.github is not None and addon_info.github.fork_source is not None:
            source_id: GithubRepoId = GithubRepoId(addon_info.github.fork_source.get_id().lower())
            if source_id != own_repo_id:
                owners: list[AddonId] = [owner for owner in repo_addons.get(source_id, []) if owner != addon_id]
                if len(owners) == 1:
                    return ForkRelation(owners[0], ForkEvidence.GITHUB_FORK)
                if ai_parent in owners:
                    return ForkRelation(ai_parent, ForkEvidence.GITHUB_FORK)
        return ForkRelation(ai_parent, ForkEvidence.AI) if ai_parent is not None else None

    @staticmethod
    def __own_repo_id(addon_info: AddonInfo) -> Optional[GithubRepoId]:
        if addon_info.github is None or addon_info.github.github_repo is None:
            return None
        return GithubRepoId(addon_info.github.github_repo.get_id().lower())
