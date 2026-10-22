from dataclasses import replace
from typing import Optional

from anki_addons_dataset.collector.ai.ai_fork_classifier import AiForkClassifier
from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText, AiInstructions
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonTitle, AiForkLabel, AiModel, GithubReadme, \
    PageLink, PageLinkSection, URL

CATALOG: dict[AddonId, AddonTitle] = {AddonId(10): AddonTitle("Original Addon"),
                                      AddonId(20): AddonTitle("Unrelated Addon"),
                                      AddonId(1312127886): AddonTitle("Own Other Addon")}


class RecordingAiProvider(AiProvider):
    def __init__(self, response: Optional[AiResponseText] = AiResponseText("10 fork_of\n20 other")):
        super().__init__(AiModel("stub-model"))
        self.__response: Optional[AiResponseText] = response
        self.prompts: list[AiPrompt] = []
        self.instructions: Optional[AiInstructions] = None

    def response(self, prompt: AiPrompt, instructions: Optional[AiInstructions] = None) -> Optional[AiResponseText]:
        self.prompts.append(prompt)
        self.instructions = instructions
        return self.__response

    def verify_access(self) -> Optional[str]:
        return None


def __classifier(provider: AiProvider, readme_max_chars: int = 8000) -> AiForkClassifier:
    return AiForkClassifier(provider, CATALOG, readme_max_chars=readme_max_chars)


def __with_links(addon_info: AddonInfo, *links: PageLink) -> AddonInfo:
    return replace(addon_info, page=replace(addon_info.page, links=list(links)))


def __with_readme(addon_info: AddonInfo, readme: str) -> AddonInfo:
    assert addon_info.github is not None
    return replace(addon_info, github=replace(addon_info.github, readme=GithubReadme(readme)))


def __link(url: str, *texts: str, section: PageLinkSection = PageLinkSection.DESCRIPTION) -> PageLink:
    return PageLink(URL(url), section, 1, list(texts))


def test_prompt_lists_the_linked_catalog_addons(addon_info: AddonInfo) -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    addon: AddonInfo = __with_links(addon_info,
                                    __link("https://ankiweb.net/shared/info/20", "see also"),
                                    __link("https://ankiweb.net/shared/info/10?ref=x", "original add-on"),
                                    __link("https://ankiweb.net/shared/info/10", "here"))

    labels: Optional[dict[AddonId, AiForkLabel]] = __classifier(provider).classify(addon)

    assert labels == {AddonId(10): AiForkLabel.FORK_OF, AddonId(20): AiForkLabel.OTHER}
    prompt: AiPrompt = provider.prompts[0]
    assert addon_info.page.description in prompt
    assert '<linked_addon id="10">\n<title>Original Addon</title>\n<link_texts>original add-on; here</link_texts>' in prompt
    assert prompt.index('id="10"') < prompt.index('id="20"')
    assert '<label name="fork_of">' in provider.instructions
    assert '<label name="based_on_code">' in provider.instructions


def test_own_author_group_unknown_and_contact_links_are_skipped(addon_info: AddonInfo) -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    addon: AddonInfo = __with_links(addon_info,
                                    __link(f"https://ankiweb.net/shared/info/{addon_info.header.id}", "self"),
                                    __link("https://ankiweb.net/shared/info/1312127886", "my other addon"),
                                    __link("https://ankiweb.net/shared/info/99", "not in catalog"),
                                    __link("https://ankiweb.net/shared/info/10", section=PageLinkSection.CONTACT_AUTHOR),
                                    __link("https://ankiweb.net/shared/decks/10", "a deck"))

    labels: Optional[dict[AddonId, AiForkLabel]] = __classifier(provider).classify(addon)

    assert labels == {}
    assert provider.prompts == []


def test_unknown_ids_and_labels_are_dropped(addon_info: AddonInfo) -> None:
    provider: RecordingAiProvider = RecordingAiProvider(AiResponseText(" 10: Fork_Of \n20 sibling\n30 fork_of\n"))
    addon: AddonInfo = __with_links(addon_info, __link("https://ankiweb.net/shared/info/10"),
                                    __link("https://ankiweb.net/shared/info/20"))

    labels: Optional[dict[AddonId, AiForkLabel]] = __classifier(provider).classify(addon)

    assert labels == {AddonId(10): AiForkLabel.FORK_OF}


def test_based_on_code_label(addon_info: AddonInfo) -> None:
    provider: RecordingAiProvider = RecordingAiProvider(AiResponseText("10 based_on_code\n20 fork_of"))
    addon: AddonInfo = __with_links(addon_info, __link("https://ankiweb.net/shared/info/10"),
                                    __link("https://ankiweb.net/shared/info/20"))

    labels: Optional[dict[AddonId, AiForkLabel]] = __classifier(provider).classify(addon)

    assert labels == {AddonId(10): AiForkLabel.BASED_ON_CODE, AddonId(20): AiForkLabel.FORK_OF}


def test_missing_answer_is_none(addon_info: AddonInfo) -> None:
    provider: RecordingAiProvider = RecordingAiProvider(None)
    addon: AddonInfo = __with_links(addon_info, __link("https://ankiweb.net/shared/info/10"))

    assert __classifier(provider).classify(addon) is None


def test_readme_links_are_candidates_and_the_readme_is_in_the_prompt(addon_info: AddonInfo) -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    addon: AddonInfo = __with_readme(addon_info, "Fork of [the original](https://ankiweb.net/shared/info/10).\n"
                                                 "See also https://ankiweb.net/shared/info/20")

    labels: Optional[dict[AddonId, AiForkLabel]] = __classifier(provider).classify(addon)

    assert labels == {AddonId(10): AiForkLabel.FORK_OF, AddonId(20): AiForkLabel.OTHER}
    prompt: AiPrompt = provider.prompts[0]
    assert "<addon_github_readme>\nFork of [the original]" in prompt
    assert '<linked_addon id="10">\n<title>Original Addon</title>\n<link_texts>the original</link_texts>' in prompt
    assert '<linked_addon id="20">\n<title>Unrelated Addon</title>\n<link_texts>None.</link_texts>' in prompt


def test_description_and_readme_links_to_one_addon_are_merged(addon_info: AddonInfo) -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    addon: AddonInfo = __with_readme(__with_links(addon_info, __link("https://ankiweb.net/shared/info/10", "here")),
                                     "Based on [Original](https://ankiweb.net/shared/info/10) "
                                     "and [here](https://ankiweb.net/shared/info/10)")

    __classifier(provider).classify(addon)

    assert provider.prompts[0].count("<linked_addon ") == 1
    assert "<link_texts>here; Original</link_texts>" in provider.prompts[0]


def test_own_author_group_and_unknown_readme_links_are_skipped(addon_info: AddonInfo) -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    addon: AddonInfo = __with_readme(addon_info, "[mine](https://ankiweb.net/shared/info/1312127886) "
                                                 "https://ankiweb.net/shared/info/99")

    assert __classifier(provider).classify(addon) == {}
    assert provider.prompts == []


def test_link_past_the_readme_limit_is_still_a_candidate(addon_info: AddonInfo) -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    addon: AddonInfo = __with_readme(addon_info, "x" * 20 + " https://ankiweb.net/shared/info/10")

    labels: Optional[dict[AddonId, AiForkLabel]] = __classifier(provider, readme_max_chars=10).classify(addon)

    assert labels == {AddonId(10): AiForkLabel.FORK_OF}
    assert "x" * 10 + "\n\n(README truncated.)" in provider.prompts[0]
    assert "x" * 11 not in provider.prompts[0]
