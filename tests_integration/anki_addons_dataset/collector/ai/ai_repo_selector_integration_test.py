import logging
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider
from anki_addons_dataset.collector.ai.ai_repo_selector import AiRepoSelector, AiRepoAnswer
from anki_addons_dataset.collector.ai.cached_ai_provider import CachedAiProvider
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId, AddonTitle, URL, AddonRating, \
    UpdateDate, AnkiVersion, AddonPage, HtmlStr, PageLink, PageLinkSection, AddonDescription, GithubInfo, GithubRepo, \
    GithubUserName, GithubRepoName, GithubReadme, AddonManifest
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)

library_repo: GithubRepo = GithubRepo(GithubUserName("kerrickstaley"), GithubRepoName("genanki"))


def __addon_info(addon_id: AddonId, own_repo: GithubRepo) -> AddonInfo:
    return AddonInfo(
        AddonHeader(addon_id, AddonTitle("Note Size"), URL(f"https://ankiweb.net/shared/info/{addon_id}"),
                    AddonRating(0), UpdateDate("2026-01-01"), AnkiVersion("25.09")),
        AddonPage(HtmlStr(""), 0, 0, [], [
            PageLink(URL(f"https://github.com/{own_repo.get_id()}"), PageLinkSection.DESCRIPTION, 1, ["Source code"]),
            PageLink(URL(f"https://github.com/{library_repo.get_id()}"), PageLinkSection.DESCRIPTION, 1,
                     ["based on"]),
        ], AddonDescription(
            "Displays the size in bytes of your collection and individual notes, including attachments.")),
        None, None)


def __own_candidate(own_repo: GithubRepo) -> GithubInfo:
    return GithubInfo([], own_repo, [], 30, None, None, None, readme=GithubReadme(
        "An addon for Anki flashcard program that shows sizes of collection and individual notes "
        "including attached files (images, audios, videos, etc.)."),
                      manifest=AddonManifest(homepage=None))


def __library_candidate() -> GithubInfo:
    return GithubInfo([], library_repo, [], 2500, None, None, None,
                      readme=GithubReadme("A Python 3 library for generating Anki decks."),
                      repo_description="A Python 3 library for generating Anki decks")


def __select(ai_provider: AiProvider, snapshot_dir: SnapshotDir, addon_info: AddonInfo,
             candidates: list[GithubInfo]) -> Optional[AiRepoAnswer]:
    cached_ai_provider: CachedAiProvider = CachedAiProvider(ai_provider, snapshot_dir.get_ai_cache_file())
    answer: Optional[AiRepoAnswer] = AiRepoSelector(cached_ai_provider).select(addon_info, candidates)
    log.info(f"Answer: {answer}")
    log.info(f"Cache hits: {cached_ai_provider.get_cache_stats().hit_count}")
    log.info(f"Cache misses: {cached_ai_provider.get_cache_stats().miss_count}")
    return answer


def test_selects_own_repo_over_library(ai_provider: AiProvider, snapshot_dir: SnapshotDir, known_addon_id: AddonId,
                                       known_github_repo: GithubRepo) -> None:
    answer: Optional[AiRepoAnswer] = __select(
        ai_provider, snapshot_dir, __addon_info(known_addon_id, known_github_repo),
        [__library_candidate(), __own_candidate(known_github_repo)])
    assert answer == AiRepoAnswer(known_github_repo)


def test_answers_none_for_library_only(ai_provider: AiProvider, snapshot_dir: SnapshotDir, known_addon_id: AddonId,
                                       known_github_repo: GithubRepo) -> None:
    answer: Optional[AiRepoAnswer] = __select(
        ai_provider, snapshot_dir, __addon_info(known_addon_id, known_github_repo), [__library_candidate()])
    assert answer == AiRepoAnswer(None)
