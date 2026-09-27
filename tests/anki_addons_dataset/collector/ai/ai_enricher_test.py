from pathlib import Path
from typing import Optional

from anki_addons_dataset.collector.ai.ai_enricher import AiEnricher
from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText
from anki_addons_dataset.collector.ai.ai_summarizer import AiSummarizer
from anki_addons_dataset.collector.ai.cached_ai_provider import CachedAiProvider
from anki_addons_dataset.collector.ai.no_ai_provider import NoAiProvider
from anki_addons_dataset.common.data_types import AddonInfo, AddonInfos, AiModel, GithubReadme

MODEL: AiModel = AiModel("test-model")


class StubAiProvider(AiProvider):
    def __init__(self, response: Optional[AiResponseText] = AiResponseText("A generated summary.")):
        super().__init__(MODEL)
        self.__response: Optional[AiResponseText] = response
        self.prompts: list[AiPrompt] = []

    def response(self, prompt: AiPrompt) -> Optional[AiResponseText]:
        self.prompts.append(prompt)
        return self.__response


def __enricher(ai_provider: AiProvider) -> AiEnricher:
    return AiEnricher(AiSummarizer(ai_provider, readme_max_chars=8000), MODEL, workers=2)


def test_summary_is_added(addon_info: AddonInfo) -> None:
    addon_info.ai = None
    enriched: AddonInfos = __enricher(StubAiProvider()).enrich(AddonInfos([addon_info]))

    assert enriched[0].ai is not None
    assert enriched[0].ai.summary == "A generated summary."
    assert enriched[0].ai.model == MODEL


def test_readme_is_taken_from_the_github_block(addon_info: AddonInfo) -> None:
    addon_info.github.readme = GithubReadme("Readme of the addon repo.")
    provider: StubAiProvider = StubAiProvider()

    __enricher(provider).enrich(AddonInfos([addon_info]))

    assert "Readme of the addon repo." in provider.prompts[0]


def test_addon_without_github_is_still_summarized(addon_info: AddonInfo) -> None:
    addon_info.github = None
    enriched: AddonInfos = __enricher(StubAiProvider()).enrich(AddonInfos([addon_info]))

    assert enriched[0].ai.summary == "A generated summary."


def test_unanswered_addon_keeps_no_summary(addon_info: AddonInfo) -> None:
    addon_info.ai = None
    enriched: AddonInfos = __enricher(StubAiProvider(response=None)).enrich(AddonInfos([addon_info]))

    assert enriched[0].ai is None


def test_other_blocks_are_preserved(addon_info: AddonInfo) -> None:
    enriched: AddonInfos = __enricher(StubAiProvider()).enrich(AddonInfos([addon_info]))

    assert enriched[0].header == addon_info.header
    assert enriched[0].page == addon_info.page
    assert enriched[0].github == addon_info.github
    assert enriched[0].forum == addon_info.forum


def test_offline_run_is_served_from_the_cache(addon_info: AddonInfo, tmp_path: Path) -> None:
    """How PARSE works: the `ai` step filled the cache, PARSE reads it back without network."""
    addon_info.ai = None
    cache_file: Path = tmp_path / "ai-cache.jsonl"
    online: CachedAiProvider = CachedAiProvider(StubAiProvider(), cache_file)
    __enricher(online).enrich(AddonInfos([addon_info]))

    offline: CachedAiProvider = CachedAiProvider(NoAiProvider(MODEL), cache_file, offline=True)
    enriched: AddonInfos = __enricher(offline).enrich(AddonInfos([addon_info]))

    assert enriched[0].ai.summary == "A generated summary."
    assert offline.get_cache_hit_count() == 1
    assert offline.get_cache_miss_count() == 0


def test_offline_miss_leaves_no_summary(addon_info: AddonInfo, tmp_path: Path) -> None:
    addon_info.ai = None
    offline: CachedAiProvider = CachedAiProvider(NoAiProvider(MODEL), tmp_path / "ai-cache.jsonl", offline=True)

    enriched: AddonInfos = __enricher(offline).enrich(AddonInfos([addon_info]))

    assert enriched[0].ai is None
    assert offline.get_cache_miss_count() == 1
