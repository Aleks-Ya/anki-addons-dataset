from dataclasses import replace
from typing import Optional
from unittest.mock import Mock

from anki_addons_dataset.collector.fork_resolver import ForkResolver
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AiForkLabel, AiInfo, ForkEvidence, \
    ForkRelation, GithubRepo, GithubRepoName, GithubUserName


def __repo(repo_id: str) -> GithubRepo:
    user, name = repo_id.split("/")
    return GithubRepo(GithubUserName(user), GithubRepoName(name))


def __addon(addon_info: AddonInfo, addon_id: int, repo: Optional[str] = None, fork_source: Optional[str] = None,
            fork_labels: Optional[dict[int, AiForkLabel]] = None) -> AddonInfo:
    github = replace(addon_info.github, github_repo=__repo(repo) if repo else None,
                     fork_source=__repo(fork_source) if fork_source else None)
    ai: AiInfo = AiInfo(fork_labels={AddonId(key): label for key, label in (fork_labels or {}).items()})
    return replace(addon_info, header=replace(addon_info.header, id=AddonId(addon_id)), github=github, ai=ai)


def __resolve(addon_infos: list[AddonInfo], fork_of: Optional[dict[int, list[int]]] = None) -> dict[int, list[ForkRelation]]:
    overrider: Mock = Mock(spec=Overrider)
    overrider.override_fork_of.side_effect = lambda addon_id: (fork_of or {}).get(addon_id)
    resolved: AddonInfos = ForkResolver(overrider).resolve(AddonInfos(addon_infos))
    return {addon_info.header.id: addon_info.forked_from for addon_info in resolved}


def test_fork_of_a_repo_owned_by_one_addon(addon_info: AddonInfo):
    forked_from: dict[int, list[ForkRelation]] = __resolve([
        __addon(addon_info, 10, "origin/pokemanki"),
        __addon(addon_info, 20, "fixer/pokemanki", fork_source="Origin/Pokemanki")])

    assert forked_from == {10: [], 20: [ForkRelation(AddonId(10), ForkEvidence.GITHUB_FORK)]}


def test_fork_of_a_monorepo_needs_the_ai_to_pick_the_parent(addon_info: AddonInfo):
    monorepo: list[AddonInfo] = [__addon(addon_info, 10, "glutanimate/misc"), __addon(addon_info, 11, "glutanimate/misc")]

    confirmed: dict[int, list[ForkRelation]] = __resolve([
        *monorepo, __addon(addon_info, 20, "fixer/misc", "glutanimate/misc", {11: AiForkLabel.FORK_OF})])
    unconfirmed: dict[int, list[ForkRelation]] = __resolve([
        *monorepo, __addon(addon_info, 20, "fixer/misc", "glutanimate/misc")])

    assert confirmed[20] == [ForkRelation(AddonId(11), ForkEvidence.GITHUB_FORK)]
    assert unconfirmed[20] == []


def test_fork_source_without_an_addon_or_equal_to_the_own_repo_is_ignored(addon_info: AddonInfo):
    forked_from: dict[int, list[ForkRelation]] = __resolve([
        __addon(addon_info, 10, "origin/a"),
        __addon(addon_info, 20, "fixer/b", fork_source="nobody/b"),
        __addon(addon_info, 30, "origin/a", fork_source="origin/a")])

    assert forked_from == {10: [], 20: [], 30: []}


def test_ai_fork_label_without_github(addon_info: AddonInfo):
    forked_from: dict[int, list[ForkRelation]] = __resolve([
        __addon(addon_info, 10),
        __addon(addon_info, 20, fork_labels={10: AiForkLabel.FORK_OF, 30: AiForkLabel.BASED_ON_IDEA,
                                             40: AiForkLabel.OTHER})])

    assert forked_from[20] == [ForkRelation(AddonId(10), ForkEvidence.AI)]


def test_github_and_ai_agreeing_keep_the_github_evidence(addon_info: AddonInfo):
    forked_from: dict[int, list[ForkRelation]] = __resolve([
        __addon(addon_info, 10, "origin/a"),
        __addon(addon_info, 20, "fixer/a", "origin/a", {10: AiForkLabel.FORK_OF})])

    assert forked_from[20] == [ForkRelation(AddonId(10), ForkEvidence.GITHUB_FORK)]


def test_override_replaces_the_detected_parents(addon_info: AddonInfo):
    addon_infos: list[AddonInfo] = [
        __addon(addon_info, 10, "origin/a"),
        __addon(addon_info, 20, "fixer/a", "origin/a"),
        __addon(addon_info, 30, fork_labels={10: AiForkLabel.FORK_OF})]

    forked_from: dict[int, list[ForkRelation]] = __resolve(addon_infos, {20: [], 30: [20, 99, 30]})

    assert forked_from == {10: [], 20: [], 30: [ForkRelation(AddonId(20), ForkEvidence.OVERRIDE)]}


def test_addon_without_github_and_ai_has_no_parent(addon_info: AddonInfo):
    addon: AddonInfo = replace(addon_info, github=None, ai=None)

    assert __resolve([addon]) == {addon_info.header.id: []}
