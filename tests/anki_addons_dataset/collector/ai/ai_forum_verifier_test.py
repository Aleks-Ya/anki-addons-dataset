from typing import Optional

import pytest

from anki_addons_dataset.collector.ai.ai_forum_verifier import AiForumVerifier, AiForumAnswer
from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText, AiInstructions
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId, AddonTitle, URL, AddonRating, \
    UpdateDate, AnkiVersion, AddonPage, HtmlStr, PageLink, PageLinkSection, AddonDescription, AiModel, \
    AnkiForumTopicContent, AnkiForumPost


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


forum_url: URL = URL("https://forums.ankiweb.net/t/anki-crashes-because-of-mpv/3359")


def __addon_info() -> AddonInfo:
    return AddonInfo(
        AddonHeader(AddonId(123456789), AddonTitle("Video Fix"), URL("https://ankiweb.net/shared/info/123456789"),
                    AddonRating(0), UpdateDate("2026-01-01"), AnkiVersion("25.09")),
        AddonPage(HtmlStr(""), 0, 0, [], [
            PageLink(URL("https://forums.ankiweb.net/t/anki-crashes-because-of-mpv/3359/5"),
                     PageLinkSection.DESCRIPTION, 1, ["this issue"]),
            PageLink(URL("https://forums.ankiweb.net/t/other-thread/42"), PageLinkSection.DESCRIPTION, 1, ["other"]),
        ], AddonDescription("Fixes the MPV crash.")),
        None, None)


def __topic() -> AnkiForumTopicContent:
    return AnkiForumTopicContent("Anki crashes because of MPV", "influencia", 13, [
        AnkiForumPost(1, "influencia", "My Anki keeps on crashing.", []),
        AnkiForumPost(2, "someone", "Me too.", []),
        AnkiForumPost(3, "author", "Try my addon " + "x" * 2000, [URL("https://ankiweb.net/shared/info/123456789")]),
        AnkiForumPost(4, "other", "Another addon", [URL("https://ankiweb.net/shared/info/1234567890")]),
    ])


@pytest.mark.parametrize("response, exp_answer", [
    ("yes", AiForumAnswer(True)),
    (" No. ", AiForumAnswer(False)),
    ("`YES`", AiForumAnswer(True)),
    ("maybe", None),
    (None, None),
])
def test_verify_answer(response: Optional[str], exp_answer: Optional[AiForumAnswer]):
    ai_provider: RecordingAiProvider = RecordingAiProvider(AiResponseText(response) if response else None)
    assert AiForumVerifier(ai_provider).verify(__addon_info(), forum_url, __topic()) == exp_answer


def test_verify_prompt():
    ai_provider: RecordingAiProvider = RecordingAiProvider(AiResponseText("no"))
    AiForumVerifier(ai_provider).verify(__addon_info(), forum_url, __topic())
    assert ai_provider.prompt is not None
    assert "<addon_title>\nVideo Fix\n</addon_title>" in ai_provider.prompt
    assert "Fixes the MPV crash." in ai_provider.prompt
    assert "<forum_link_texts>this issue</forum_link_texts>" in ai_provider.prompt
    assert "<topic_title>Anki crashes because of MPV</topic_title>" in ai_provider.prompt
    assert "<created_by>influencia</created_by>" in ai_provider.prompt
    assert "<posts_count>13</posts_count>" in ai_provider.prompt
    assert '<post number="1" author="influencia" links_this_addon="no">' in ai_provider.prompt
    assert '<post number="3" author="author" links_this_addon="yes">' in ai_provider.prompt
    assert "(post truncated)" in ai_provider.prompt
    assert 'number="2"' not in ai_provider.prompt
    assert 'number="4"' not in ai_provider.prompt


def test_verify_instructions():
    ai_provider: RecordingAiProvider = RecordingAiProvider(AiResponseText("yes"))
    AiForumVerifier(ai_provider).verify(__addon_info(), forum_url, __topic())
    assert ai_provider.instructions is not None
    assert "announced, released or supported" in ai_provider.instructions
    assert "Output only the word yes or the word no" in ai_provider.instructions


def test_verify_without_link_texts():
    addon_info: AddonInfo = __addon_info()
    ai_provider: RecordingAiProvider = RecordingAiProvider(AiResponseText("yes"))
    AiForumVerifier(ai_provider).verify(addon_info, URL("https://forums.ankiweb.net/t/unlinked/7"), __topic())
    assert ai_provider.prompt is not None
    assert "<forum_link_texts>None.</forum_link_texts>" in ai_provider.prompt
