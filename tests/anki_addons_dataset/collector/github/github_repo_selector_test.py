from typing import Optional
from unittest.mock import Mock

from anki_addons_dataset.collector.ai.question.ai_repo_selector import AiRepoSelector, AiRepoAnswer
from anki_addons_dataset.collector.github.github_repo_selector import GithubRepoSelector
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.collector.url_parser import UrlParser
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId, AddonTitle, URL, AddonRating, \
    UpdateDate, AnkiVersion, AddonPage, HtmlStr, GithubInfo, GithubRepo, GithubUserName, GithubRepoName, \
    GithubReadme, GithubRepoSource, GitHubLink, AddonManifest

addon_id: AddonId = AddonId(123456789)
own_repo: GithubRepo = GithubRepo(GithubUserName("author"), GithubRepoName("my-addon"))
library_repo: GithubRepo = GithubRepo(GithubUserName("kerrickstaley"), GithubRepoName("genanki"))


def __links(*urls: str) -> list[GitHubLink]:
    return UrlParser.find_github_links([URL(url) for url in urls])


def __addon_info(github_links: list[GitHubLink]) -> AddonInfo:
    return AddonInfo(
        AddonHeader(addon_id, AddonTitle("My Addon"), URL(f"https://ankiweb.net/shared/info/{addon_id}"),
                    AddonRating(0), UpdateDate("2026-01-01"), AnkiVersion("25.09")),
        AddonPage(HtmlStr(""), 0, 0, [], []),
        GithubInfo(github_links, None, [], 0, None, None, None), None)


def __candidate(repo: GithubRepo, readme: Optional[str] = None,
                manifest: Optional[AddonManifest] = None) -> GithubInfo:
    return GithubInfo([], repo, [], 0, None, None, None, readme=GithubReadme(readme) if readme else None,
                      manifest=manifest)


def __ai(answer: Optional[AiRepoAnswer]) -> Mock:
    ai_repo_selector: Mock = Mock(spec=AiRepoSelector)
    ai_repo_selector.select.return_value = answer
    return ai_repo_selector


library_links: list[GitHubLink] = __links("https://github.com/kerrickstaley/genanki",
                                          "https://github.com/kerrickstaley/genanki/issues",
                                          "https://github.com/author/my-addon")


def test_candidate_repos_are_distinct_and_skip_user_links(overrider: Overrider) -> None:
    selector: GithubRepoSelector = GithubRepoSelector(overrider, None)
    links: list[GitHubLink] = __links("https://github.com/author/my-addon/issues", "https://github.com/author",
                                      "https://github.com/author/my-addon", "https://github.com/kerrickstaley/genanki")
    assert selector.candidate_repos(links) == [own_repo, library_repo]


def test_no_candidates(overrider: Overrider) -> None:
    ai_repo_selector: Mock = __ai(AiRepoAnswer(own_repo))
    assert GithubRepoSelector(overrider, ai_repo_selector).select(__addon_info([]), []) is None
    ai_repo_selector.select.assert_not_called()


def test_self_reference_wins_without_ai(overrider: Overrider) -> None:
    ai_repo_selector: Mock = __ai(AiRepoAnswer(library_repo))
    candidates: list[GithubInfo] = [__candidate(library_repo, "Generate Anki decks"),
                                    __candidate(own_repo, f"Install with code {addon_id}")]
    selected: Optional[GithubInfo] = GithubRepoSelector(overrider, ai_repo_selector).select(
        __addon_info(library_links), candidates)
    assert selected.github_repo == own_repo
    assert selected.repo_source == GithubRepoSource.SELF_REFERENCE
    ai_repo_selector.select.assert_not_called()


def test_self_reference_in_manifest_homepage(overrider: Overrider) -> None:
    manifest: AddonManifest = AddonManifest(homepage=f"https://ankiweb.net/shared/info/{addon_id}")
    selected: Optional[GithubInfo] = GithubRepoSelector(overrider, None).select(
        __addon_info(library_links), [__candidate(library_repo), __candidate(own_repo, manifest=manifest)])
    assert selected.repo_source == GithubRepoSource.SELF_REFERENCE


def test_longer_number_is_not_a_self_reference(overrider: Overrider) -> None:
    selected: Optional[GithubInfo] = GithubRepoSelector(overrider, None).select(
        __addon_info(library_links), [__candidate(library_repo, f"Ticket {addon_id}0"), __candidate(own_repo)])
    assert selected.repo_source == GithubRepoSource.MOST_LINKED


def test_ai_chooses_when_no_self_reference(overrider: Overrider) -> None:
    selected: Optional[GithubInfo] = GithubRepoSelector(overrider, __ai(AiRepoAnswer(own_repo))).select(
        __addon_info(library_links), [__candidate(library_repo), __candidate(own_repo)])
    assert selected.github_repo == own_repo
    assert selected.repo_source == GithubRepoSource.AI


def test_ai_judges_a_single_candidate(overrider: Overrider) -> None:
    ai_repo_selector: Mock = __ai(AiRepoAnswer(None))
    selected: Optional[GithubInfo] = GithubRepoSelector(overrider, ai_repo_selector).select(
        __addon_info(__links("https://github.com/kerrickstaley/genanki")), [__candidate(library_repo)])
    assert selected is None
    ai_repo_selector.select.assert_called_once()


def test_ai_miss_falls_back_to_most_linked(overrider: Overrider) -> None:
    selected: Optional[GithubInfo] = GithubRepoSelector(overrider, __ai(None)).select(
        __addon_info(library_links), [__candidate(own_repo), __candidate(library_repo)])
    assert selected.github_repo == library_repo
    assert selected.repo_source == GithubRepoSource.MOST_LINKED


def test_without_ai_falls_back_to_most_linked(overrider: Overrider) -> None:
    selected: Optional[GithubInfo] = GithubRepoSelector(overrider, None).select(
        __addon_info(library_links), [__candidate(own_repo), __candidate(library_repo)])
    assert selected.github_repo == library_repo
    assert selected.repo_source == GithubRepoSource.MOST_LINKED
