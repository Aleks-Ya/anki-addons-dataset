from pathlib import Path
from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider
from anki_addons_dataset.collector.ai.ai_summarizer import AiSummarizer
from anki_addons_dataset.collector.ai.cached_ai_provider import CachedAiProvider
from anki_addons_dataset.collector.ai.deepseek_ai_provider import DeepSeekAiProvider
from anki_addons_dataset.common.data_types import AddonTitle, AddonDescription, GithubReadme, AiModel, AiSummary


def test_summarize(tmp_path: Path) -> None:
    endpoint: str = "https://api.deepseek.com"
    api_key: str = Path("/home/aleks/.config/anki-addons-dataset/deepseek-api-key.txt").read_text().strip()
    model: AiModel = AiModel("deepseek-flash")
    deepseek_ai_provider: AiProvider = DeepSeekAiProvider(endpoint, api_key, model)
    cached_ai_provider: CachedAiProvider = CachedAiProvider(deepseek_ai_provider, tmp_path / "ai-cache.jsonl")
    assert cached_ai_provider.get_cache_hit_count() == 0
    assert cached_ai_provider.get_cache_miss_count() == 0

    ai_summarizer: AiSummarizer = AiSummarizer(cached_ai_provider)
    title: AddonTitle = AddonTitle("Note Size anki addon")
    description: AddonDescription = AddonDescription(
        """
        "Note Size" addon displays detailed information about size ("in bytes") of your collection and individual notes including attachments.
        """)
    readme: GithubReadme = GithubReadme(
        """
        An addon for Anki flashcard program that shows sizes of collection and individual notes including attached files (images, audios, videos, etc.).
        See User Manual for details.
        """)
    summary: Optional[AiSummary] = ai_summarizer.summarize(title, description, readme)
    print(summary)
    print(f"Cache hits: {cached_ai_provider.get_cache_hit_count()}")
    print(f"Cache misses: {cached_ai_provider.get_cache_miss_count()}")
