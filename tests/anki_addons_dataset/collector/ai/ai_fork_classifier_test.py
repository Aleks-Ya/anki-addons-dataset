from dataclasses import replace
from typing import Optional

from anki_addons_dataset.collector.ai.ai_fork_classifier import AiForkClassifier
from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText, AiInstructions
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonTitle, AiForkLabel, AiModel, PageLink, \
    PageLinkSection, URL

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


def __with_links(addon_info: AddonInfo, *links: PageLink) -> AddonInfo:
    return replace(addon_info, page=replace(addon_info.page, links=list(links)))


def __link(url: str, *texts: str, section: PageLinkSection = PageLinkSection.DESCRIPTION) -> PageLink:
    return PageLink(URL(url), section, 1, list(texts))


def test_prompt_lists_the_linked_catalog_addons(addon_info: AddonInfo) -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    addon: AddonInfo = __with_links(addon_info,
                                    __link("https://ankiweb.net/shared/info/20", "see also"),
                                    __link("https://ankiweb.net/shared/info/10?ref=x", "original add-on"),
                                    __link("https://ankiweb.net/shared/info/10", "here"))

    labels: Optional[dict[AddonId, AiForkLabel]] = AiForkClassifier(provider, CATALOG).classify(addon)

    assert labels == {AddonId(10): AiForkLabel.FORK_OF, AddonId(20): AiForkLabel.OTHER}
    prompt: AiPrompt = provider.prompts[0]
    assert addon_info.page.description in prompt
    assert '<linked_addon id="10">\n<title>Original Addon</title>\n<link_texts>original add-on; here</link_texts>' in prompt
    assert prompt.index('id="10"') < prompt.index('id="20"')
    assert '<label name="fork_of">' in provider.instructions


def test_own_author_group_unknown_and_contact_links_are_skipped(addon_info: AddonInfo) -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    addon: AddonInfo = __with_links(addon_info,
                                    __link(f"https://ankiweb.net/shared/info/{addon_info.header.id}", "self"),
                                    __link("https://ankiweb.net/shared/info/1312127886", "my other addon"),
                                    __link("https://ankiweb.net/shared/info/99", "not in catalog"),
                                    __link("https://ankiweb.net/shared/info/10", section=PageLinkSection.CONTACT_AUTHOR),
                                    __link("https://ankiweb.net/shared/decks/10", "a deck"))

    labels: Optional[dict[AddonId, AiForkLabel]] = AiForkClassifier(provider, CATALOG).classify(addon)

    assert labels == {}
    assert provider.prompts == []


def test_unknown_ids_and_labels_are_dropped(addon_info: AddonInfo) -> None:
    provider: RecordingAiProvider = RecordingAiProvider(AiResponseText(" 10: Fork_Of \n20 sibling\n30 fork_of\n"))
    addon: AddonInfo = __with_links(addon_info, __link("https://ankiweb.net/shared/info/10"),
                                    __link("https://ankiweb.net/shared/info/20"))

    labels: Optional[dict[AddonId, AiForkLabel]] = AiForkClassifier(provider, CATALOG).classify(addon)

    assert labels == {AddonId(10): AiForkLabel.FORK_OF}


def test_missing_answer_is_none(addon_info: AddonInfo) -> None:
    provider: RecordingAiProvider = RecordingAiProvider(None)
    addon: AddonInfo = __with_links(addon_info, __link("https://ankiweb.net/shared/info/10"))

    assert AiForkClassifier(provider, CATALOG).classify(addon) is None
