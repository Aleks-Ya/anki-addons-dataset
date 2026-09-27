from pathlib import Path
from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider
from anki_addons_dataset.collector.ai.ai_summarizer import AiSummarizer
from anki_addons_dataset.collector.ai.cached_ai_provider import CachedAiProvider
from anki_addons_dataset.common.data_types import AddonTitle, AddonDescription, GithubReadme, AiSummary
from anki_addons_dataset.common.working_dir import SnapshotDir
from anki_addons_dataset.config.app_config import AppConfig


def test_summarize(ai_provider: AiProvider, integration_config: AppConfig, snapshot_dir: SnapshotDir) -> None:
    cache_file: Path = snapshot_dir.get_ai_cache_file()
    cached_ai_provider: CachedAiProvider = CachedAiProvider(ai_provider, cache_file)
    assert cached_ai_provider.get_cache_stats().hit_count == 0
    assert cached_ai_provider.get_cache_stats().miss_count == 0

    ai_summarizer: AiSummarizer = AiSummarizer(cached_ai_provider, integration_config.ai.readme_max_chars)
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
    print(f"Cache hits: {cached_ai_provider.get_cache_stats().hit_count}")
    print(f"Cache misses: {cached_ai_provider.get_cache_stats().miss_count}")
    assert summary is not None
