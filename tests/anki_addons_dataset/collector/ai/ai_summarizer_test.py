from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText
from anki_addons_dataset.collector.ai.ai_summarizer import AiSummarizer
from anki_addons_dataset.common.data_types import AddonTitle, AddonDescription, GithubReadme, AiModel, AiSummary


class RecordingAiProvider(AiProvider):
    def __init__(self, response: Optional[AiResponseText] = AiResponseText("A summary.")):
        super().__init__(AiModel("stub-model"))
        self.__response: Optional[AiResponseText] = response
        self.prompt: Optional[AiPrompt] = None

    def response(self, prompt: AiPrompt) -> Optional[AiResponseText]:
        self.prompt = prompt
        return self.__response


def test_prompt_carries_the_addon_texts() -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    summarizer: AiSummarizer = AiSummarizer(provider, readme_max_chars=8000)

    summary: Optional[AiSummary] = summarizer.summarize(
        AddonTitle("Note Size"), AddonDescription("Displays the size of notes."), GithubReadme("A README."))

    assert summary == "A summary."
    assert "Note Size" in provider.prompt
    assert "Displays the size of notes." in provider.prompt
    assert "A README." in provider.prompt


def test_missing_readme_is_stated_in_the_prompt() -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    summarizer: AiSummarizer = AiSummarizer(provider, readme_max_chars=8000)

    summarizer.summarize(AddonTitle("Note Size"), AddonDescription("Displays the size of notes."), None)

    assert "No README provided." in provider.prompt


def test_missing_description_is_stated_in_the_prompt() -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    summarizer: AiSummarizer = AiSummarizer(provider, readme_max_chars=8000)

    summarizer.summarize(AddonTitle("Note Size"), AddonDescription(""), GithubReadme("A README."))

    assert "No description provided." in provider.prompt


def test_long_readme_is_truncated() -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    summarizer: AiSummarizer = AiSummarizer(provider, readme_max_chars=10)

    summarizer.summarize(AddonTitle("Note Size"), AddonDescription("Displays the size of notes."),
                         GithubReadme("0123456789-this-part-is-dropped"))

    assert "0123456789" in provider.prompt
    assert "dropped" not in provider.prompt
    assert "(README truncated.)" in provider.prompt


def test_short_readme_is_kept_whole() -> None:
    provider: RecordingAiProvider = RecordingAiProvider()
    summarizer: AiSummarizer = AiSummarizer(provider, readme_max_chars=10)

    summarizer.summarize(AddonTitle("Note Size"), AddonDescription("Displays the size of notes."),
                         GithubReadme("0123456789"))

    assert "0123456789" in provider.prompt
    assert "truncated" not in provider.prompt


def test_no_response_yields_no_summary() -> None:
    provider: RecordingAiProvider = RecordingAiProvider(response=None)
    summarizer: AiSummarizer = AiSummarizer(provider, readme_max_chars=8000)

    summary: Optional[AiSummary] = summarizer.summarize(
        AddonTitle("Note Size"), AddonDescription("Displays the size of notes."), GithubReadme("A README."))

    assert summary is None


def test_response_is_stripped() -> None:
    provider: RecordingAiProvider = RecordingAiProvider(AiResponseText("  A summary.\n"))
    summarizer: AiSummarizer = AiSummarizer(provider, readme_max_chars=8000)

    summary: Optional[AiSummary] = summarizer.summarize(
        AddonTitle("Note Size"), AddonDescription("Displays the size of notes."), GithubReadme("A README."))

    assert summary == "A summary."


def test_blank_response_yields_no_summary() -> None:
    provider: RecordingAiProvider = RecordingAiProvider(AiResponseText("\n  "))
    summarizer: AiSummarizer = AiSummarizer(provider, readme_max_chars=8000)

    summary: Optional[AiSummary] = summarizer.summarize(
        AddonTitle("Note Size"), AddonDescription("Displays the size of notes."), GithubReadme("A README."))

    assert summary is None
