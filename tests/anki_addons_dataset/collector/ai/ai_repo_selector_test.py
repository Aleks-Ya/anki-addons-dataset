from typing import Optional

import pytest

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText, AiInstructions
from anki_addons_dataset.collector.ai.ai_repo_selector import AiRepoSelector, AiRepoAnswer
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId, AddonTitle, URL, AddonRating, \
    UpdateDate, AnkiVersion, AddonPage, HtmlStr, PageLink, PageLinkSection, AddonDescription, GithubInfo, GithubRepo, \
    GithubUserName, GithubRepoName, GithubReadme, AiModel


class RecordingAiProvider(AiProvider):
    def __init__(self, response: Optional[AiResponseText]):
        super().__init__(AiModel("stub-model"))
        self.__response: Optional[AiResponseText] = response
        self.prompt: Optional[AiPrompt] = None
        self.instructions: Optional[AiInstructions] = None

    def response(self, prompt: AiPrompt, instructions: Optional[AiInstructions] = None) -> Optional[AiResponseText]:
        self.prompt = prompt
        self.instructions = instructions
        return self.__response

    def verify_access(self) -> Optional[str]:
        return None


own_repo: GithubRepo = GithubRepo(GithubUserName("author"), GithubRepoName("my-addon"))
library_repo: GithubRepo = GithubRepo(GithubUserName("kerrickstaley"), GithubRepoName("genanki"))


def __addon_info() -> AddonInfo:
    return AddonInfo(
        AddonHeader(AddonId(123456789), AddonTitle("My Addon"), URL("https://ankiweb.net/shared/info/123456789"),
                    AddonRating(0), UpdateDate("2026-01-01"), AnkiVersion("25.09")),
        AddonPage(HtmlStr(""), 0, 0, [], [
            PageLink(URL("https://github.com/Author/my-addon/issues"), PageLinkSection.DESCRIPTION, 1, ["Bug tracker"]),
            PageLink(URL("https://github.com/kerrickstaley/genanki"), PageLinkSection.DESCRIPTION, 1, ["based on"]),
        ], AddonDescription("Creates decks.")),
        None, None)


def __candidates() -> list[GithubInfo]:
    return [GithubInfo([], own_repo, [], 3, None, None, None, readme=GithubReadme("Own README")),
            GithubInfo([], library_repo, [], 2000, None, None, None, repo_description="Python library")]


def __select(response: Optional[str]) -> Optional[AiRepoAnswer]:
    provider: RecordingAiProvider = RecordingAiProvider(AiResponseText(response) if response is not None else None)
    return AiRepoSelector(provider).select(__addon_info(), __candidates())


def test_prompt_carries_the_addon_and_candidates() -> None:
    provider: RecordingAiProvider = RecordingAiProvider(AiResponseText("none"))
    AiRepoSelector(provider).select(__addon_info(), __candidates())
    assert "My Addon" in provider.prompt
    assert "Creates decks." in provider.prompt
    assert '<candidate repo="author/my-addon">' in provider.prompt
    assert '<candidate repo="kerrickstaley/genanki">' in provider.prompt
    assert "<link_texts>Bug tracker</link_texts>" in provider.prompt
    assert "<link_texts>based on</link_texts>" in provider.prompt
    assert "Own README" in provider.prompt
    assert "Python library" in provider.prompt
    assert "source code of this exact addon" in provider.instructions


@pytest.mark.parametrize("response", ["author/my-addon", "Author/My-Addon", "`author/my-addon`",
                                      "https://github.com/author/my-addon", " author/my-addon.\n"])
def test_answer_names_a_candidate(response: str) -> None:
    assert __select(response) == AiRepoAnswer(own_repo)


@pytest.mark.parametrize("response", ["none", "None", "NONE."])
def test_answer_none(response: str) -> None:
    assert __select(response) == AiRepoAnswer(None)


@pytest.mark.parametrize("response", ["someone/else", "I think it is author/my-addon", ""])
def test_unknown_answer_is_dropped(response: str) -> None:
    assert __select(response) is None


def test_missing_answer() -> None:
    assert __select(None) is None
