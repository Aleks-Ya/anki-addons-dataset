from dataclasses import replace
from typing import Optional
from unittest.mock import Mock

from anki_addons_dataset.collector.fork_resolver import ForkResolver
from anki_addons_dataset.collector.overrider.overrider import Overrider, ForkOverride
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AiInfo, ForkEvidence, ForkRelation, \
    GithubRepo, GithubRepoName, GithubUserName


def __repo(repo_id: str) -> GithubRepo:
    user, name = repo_id.split("/")
    return GithubRepo(GithubUserName(user), GithubRepoName(name))


def __addon(addon_info: AddonInfo, addon_id: int, repo: Optional[str] = None, fork_source: Optional[str] = None,
            ai_fork_of: Optional[int] = None) -> AddonInfo:
    github = replace(addon_info.github, github_repo=__repo(repo) if repo else None,
                     fork_source=__repo(fork_source) if fork_source else None)
    ai: AiInfo = AiInfo(fork_of=AddonId(ai_fork_of) if ai_fork_of is not None else None)
    return replace(addon_info, header=replace(addon_info.header, id=AddonId(addon_id)), github=github, ai=ai)


def __resolve(addon_infos: list[AddonInfo],
              fork_of: Optional[dict[int, Optional[int]]] = None) -> dict[int, Optional[ForkRelation]]:
    overrider: Mock = Mock(spec=Overrider)
    overrides: dict[int, Optional[int]] = fork_of or {}
    overrider.override_fork_of.side_effect = lambda addon_id: ForkOverride(
        AddonId(overrides[addon_id]) if overrides[addon_id] is not None else None) if addon_id in overrides else None
    resolved: AddonInfos = ForkResolver(overrider).resolve(AddonInfos(addon_infos))
    return {addon_info.header.id: addon_info.forked_from for addon_info in resolved}


def test_fork_of_a_repo_owned_by_one_addon(addon_info: AddonInfo):
    forked_from: dict[int, Optional[ForkRelation]] = __resolve([
        __addon(addon_info, 10, "origin/pokemanki"),
        __addon(addon_info, 20, "fixer/pokemanki", fork_source="Origin/Pokemanki")])

    assert forked_from == {10: None, 20: ForkRelation(AddonId(10), ForkEvidence.GITHUB_FORK)}


def test_fork_of_a_monorepo_needs_the_ai_to_pick_the_parent(addon_info: AddonInfo):
    monorepo: list[AddonInfo] = [__addon(addon_info, 10, "glutanimate/misc"), __addon(addon_info, 11, "glutanimate/misc")]

    confirmed: dict[int, Optional[ForkRelation]] = __resolve([
        *monorepo, __addon(addon_info, 20, "fixer/misc", "glutanimate/misc", 11)])
    unconfirmed: dict[int, Optional[ForkRelation]] = __resolve([
        *monorepo, __addon(addon_info, 20, "fixer/misc", "glutanimate/misc")])

    assert confirmed[20] == ForkRelation(AddonId(11), ForkEvidence.GITHUB_FORK)
    assert unconfirmed[20] is None


def test_fork_source_without_an_addon_or_equal_to_the_own_repo_is_ignored(addon_info: AddonInfo):
    forked_from: dict[int, Optional[ForkRelation]] = __resolve([
        __addon(addon_info, 10, "origin/a"),
        __addon(addon_info, 20, "fixer/b", fork_source="nobody/b"),
        __addon(addon_info, 30, "origin/a", fork_source="origin/a")])

    assert forked_from == {10: None, 20: None, 30: None}


def test_ai_parent_without_github(addon_info: AddonInfo):
    forked_from: dict[int, Optional[ForkRelation]] = __resolve([
        __addon(addon_info, 10),
        __addon(addon_info, 20, ai_fork_of=10)])

    assert forked_from[20] == ForkRelation(AddonId(10), ForkEvidence.AI)


def test_ai_parent_equal_to_the_addon_itself_is_ignored(addon_info: AddonInfo):
    assert __resolve([__addon(addon_info, 20, ai_fork_of=20)]) == {20: None}


def test_github_and_ai_agreeing_keep_the_github_evidence(addon_info: AddonInfo):
    forked_from: dict[int, Optional[ForkRelation]] = __resolve([
        __addon(addon_info, 10, "origin/a"),
        __addon(addon_info, 20, "fixer/a", "origin/a", 10)])

    assert forked_from[20] == ForkRelation(AddonId(10), ForkEvidence.GITHUB_FORK)


def test_github_wins_when_the_ai_names_another_parent(addon_info: AddonInfo):
    forked_from: dict[int, Optional[ForkRelation]] = __resolve([
        __addon(addon_info, 10, "origin/a"),
        __addon(addon_info, 15),
        __addon(addon_info, 20, "fixer/a", "origin/a", 15)])

    assert forked_from[20] == ForkRelation(AddonId(10), ForkEvidence.GITHUB_FORK)


def test_one_parent_can_have_several_forks(addon_info: AddonInfo):
    forked_from: dict[int, Optional[ForkRelation]] = __resolve([
        __addon(addon_info, 10, "origin/a"),
        __addon(addon_info, 20, "fixer/a", "origin/a"),
        __addon(addon_info, 30, ai_fork_of=10)])

    assert forked_from == {10: None,
                           20: ForkRelation(AddonId(10), ForkEvidence.GITHUB_FORK),
                           30: ForkRelation(AddonId(10), ForkEvidence.AI)}


def test_override_replaces_the_detected_parent(addon_info: AddonInfo):
    addon_infos: list[AddonInfo] = [
        __addon(addon_info, 10, "origin/a"),
        __addon(addon_info, 20, "fixer/a", "origin/a"),
        __addon(addon_info, 30, ai_fork_of=10),
        __addon(addon_info, 40, ai_fork_of=10),
        __addon(addon_info, 50, ai_fork_of=10)]

    forked_from: dict[int, Optional[ForkRelation]] = __resolve(addon_infos, {20: None, 30: 20, 40: 99, 50: 50})

    assert forked_from == {10: None, 20: None, 30: ForkRelation(AddonId(20), ForkEvidence.OVERRIDE), 40: None,
                           50: None}


def test_addon_without_github_and_ai_has_no_parent(addon_info: AddonInfo):
    addon: AddonInfo = replace(addon_info, github=None, ai=None)

    assert __resolve([addon]) == {addon_info.header.id: None}


def test_github_fork_owners(addon_info: AddonInfo):
    owners: dict[AddonId, list[AddonId]] = ForkResolver.github_fork_owners(AddonInfos([
        __addon(addon_info, 10, "glutanimate/misc"),
        __addon(addon_info, 11, "glutanimate/misc", fork_source="other/misc"),
        __addon(addon_info, 20, "fixer/misc", fork_source="Glutanimate/Misc"),
        __addon(addon_info, 30, "glutanimate/misc", fork_source="glutanimate/misc"),
        __addon(addon_info, 40, "fixer/b", fork_source="nobody/b")]))

    assert owners == {AddonId(20): [AddonId(10), AddonId(11), AddonId(30)]}


def test_github_parent():
    assert ForkResolver.github_parent([AddonId(10)], AddonId(20)) == AddonId(10)
    assert ForkResolver.github_parent([AddonId(10), AddonId(11)], AddonId(11)) == AddonId(11)
    assert ForkResolver.github_parent([AddonId(10), AddonId(11)], AddonId(20)) is None
    assert ForkResolver.github_parent([], AddonId(20)) is None
