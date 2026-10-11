import hashlib
from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText, AiInstructions
from anki_addons_dataset.collector.ai.ai_tagger import AiTagger
from anki_addons_dataset.common.data_types import AddonTitle, AddonDescription, GithubReadme, AiModel, AiTag


class RecordingAiProvider(AiProvider):
    def __init__(self, response: Optional[AiResponseText] = AiResponseText("statistics")):
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


def __tag(response: Optional[AiResponseText]) -> Optional[list[AiTag]]:
    tagger: AiTagger = AiTagger(RecordingAiProvider(response), readme_max_chars=8000)
    return tagger.tag(AddonTitle("Note Size"), AddonDescription("Displays the size of notes."),
                      GithubReadme("A README."))


def test_prompt_carries_the_addon_texts() -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    tagger: AiTagger = AiTagger(provider, readme_max_chars=8000)

    tags: Optional[list[AiTag]] = tagger.tag(
        AddonTitle("Note Size"), AddonDescription("Displays the size of notes."), GithubReadme("A README."))

    assert tags == ["statistics"]
    assert "Note Size" in provider.prompt
    assert "Displays the size of notes." in provider.prompt
    assert "A README." in provider.prompt


def test_prompt_lists_the_tags() -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    tagger: AiTagger = AiTagger(provider, readme_max_chars=8000)

    tagger.tag(AddonTitle("Note Size"), AddonDescription("Displays the size of notes."), None)

    assert '<tag name="card-creation">' in provider.instructions
    assert '<tag name="accessibility">' in provider.instructions
    assert '<tag name="no-description">' in provider.instructions
    assert '<tag name="beta">' in provider.instructions
    assert provider.instructions.count("<tag name=") == 39


def test_instructions_text_is_stable() -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    tagger: AiTagger = AiTagger(provider, readme_max_chars=8000)

    tagger.tag(AddonTitle("Note Size"), AddonDescription("Displays the size of notes."), None)

    assert (hashlib.sha256(provider.instructions.encode()).hexdigest() ==
            "bde259bee9b8127a0f2b87bf573885f67ba2f977bad47765b1604300106c9ce7")


def test_instructions_hold_no_addon_texts_and_prompt_holds_no_tags() -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    tagger: AiTagger = AiTagger(provider, readme_max_chars=8000)

    tagger.tag(AddonTitle("Note Size"), AddonDescription("Displays the size of notes."), GithubReadme("A README."))

    assert "Note Size" not in provider.instructions
    assert "Displays the size of notes." not in provider.instructions
    assert "A README." not in provider.instructions
    assert "<tag name=" not in provider.prompt
    assert "<guideline>" not in provider.prompt


def test_instructions_are_the_same_for_every_addon() -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    tagger: AiTagger = AiTagger(provider, readme_max_chars=8000)

    tagger.tag(AddonTitle("Note Size"), AddonDescription("Displays the size of notes."), None)
    first: Optional[AiInstructions] = provider.instructions
    tagger.tag(AddonTitle("Heatmap"), AddonDescription("Shows a review heatmap."), GithubReadme("A README."))

    assert provider.instructions == first


def test_missing_readme_is_stated_in_the_prompt() -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    tagger: AiTagger = AiTagger(provider, readme_max_chars=8000)

    tagger.tag(AddonTitle("Note Size"), AddonDescription("Displays the size of notes."), None)

    assert "No README provided." in provider.prompt


def test_missing_description_is_stated_in_the_prompt() -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    tagger: AiTagger = AiTagger(provider, readme_max_chars=8000)

    tagger.tag(AddonTitle("Note Size"), AddonDescription(""), GithubReadme("A README."))

    assert "No description provided." in provider.prompt


def test_long_readme_is_truncated() -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    tagger: AiTagger = AiTagger(provider, readme_max_chars=10)

    tagger.tag(AddonTitle("Note Size"), AddonDescription("Displays the size of notes."),
               GithubReadme("0123456789-this-part-is-dropped"))

    assert "0123456789" in provider.prompt
    assert "dropped" not in provider.prompt
    assert "(README truncated.)" in provider.prompt


def test_short_readme_is_kept_whole() -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    tagger: AiTagger = AiTagger(provider, readme_max_chars=10)

    tagger.tag(AddonTitle("Note Size"), AddonDescription("Displays the size of notes."),
               GithubReadme("0123456789"))

    assert "0123456789" in provider.prompt
    assert "truncated" not in provider.prompt


def test_comma_separated_tags_are_parsed() -> None:
    assert __tag(AiResponseText("scheduling, fsrs")) == ["scheduling", "fsrs"]


def test_tags_are_normalized() -> None:
    assert __tag(AiResponseText("  Scheduling ,\nFSRS\n")) == ["scheduling", "fsrs"]


def test_unknown_tags_are_dropped() -> None:
    assert __tag(AiResponseText("scheduling, flashcards, fsrs")) == ["scheduling", "fsrs"]


def test_duplicate_tags_are_removed() -> None:
    assert __tag(AiResponseText("fsrs, scheduling, fsrs")) == ["scheduling", "fsrs"]


def test_tags_follow_the_declared_order() -> None:
    assert __tag(AiResponseText("paid, ai")) == ["ai", "paid"]


def test_no_response_yields_no_tags() -> None:
    assert __tag(None) is None


def test_blank_response_yields_no_tags() -> None:
    assert __tag(AiResponseText("\n  ")) is None


def test_only_unknown_tags_yield_no_tags() -> None:
    assert __tag(AiResponseText("flashcards, misc")) is None
