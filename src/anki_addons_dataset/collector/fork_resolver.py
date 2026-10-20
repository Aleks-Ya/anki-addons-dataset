import copy
import logging
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AiForkLabel, ForkEvidence, \
    ForkRelation, GithubRepoId

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
            override: Optional[list[AddonId]] = self.__overrider.override_fork_of(addon_info.header.id)
            if override is not None:
                forked_from: list[ForkRelation] = [ForkRelation(parent_id, ForkEvidence.OVERRIDE)
                                                   for parent_id in sorted(set(override))
                                                   if parent_id in catalog and parent_id != addon_info.header.id]
            else:
                forked_from = ForkResolver.__detect(addon_info, repo_addons)
            resolved.append(copy.replace(addon_info, forked_from=forked_from))
        log.info(f"Addons with a detected parent: {sum(1 for addon_info in resolved if addon_info.forked_from)}")
        return AddonInfos(resolved)

    @staticmethod
    def __detect(addon_info: AddonInfo, repo_addons: dict[GithubRepoId, list[AddonId]]) -> list[ForkRelation]:
        addon_id: AddonId = addon_info.header.id
        ai_parents: set[AddonId] = {parent_id for parent_id, label in (addon_info.ai.fork_labels if addon_info.ai else {})
                                    .items() if label == AiForkLabel.FORK_OF and parent_id != addon_id}
        github_parents: set[AddonId] = set()
        own_repo_id: Optional[GithubRepoId] = ForkResolver.__own_repo_id(addon_info)
        if addon_info.github is not None and addon_info.github.fork_source is not None:
            source_id: GithubRepoId = GithubRepoId(addon_info.github.fork_source.get_id().lower())
            if source_id != own_repo_id:
                owners: list[AddonId] = [owner for owner in repo_addons.get(source_id, []) if owner != addon_id]
                github_parents = set(owners) if len(owners) == 1 else set(owners) & ai_parents
        relations: list[ForkRelation] = [ForkRelation(parent_id, ForkEvidence.GITHUB_FORK)
                                         for parent_id in github_parents]
        relations.extend(ForkRelation(parent_id, ForkEvidence.AI) for parent_id in ai_parents - github_parents)
        return sorted(relations, key=lambda relation: relation.addon_id)

    @staticmethod
    def __own_repo_id(addon_info: AddonInfo) -> Optional[GithubRepoId]:
        if addon_info.github is None or addon_info.github.github_repo is None:
            return None
        return GithubRepoId(addon_info.github.github_repo.get_id().lower())
