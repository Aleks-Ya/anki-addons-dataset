import logging
from logging import Logger
from pathlib import Path
from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider
from anki_addons_dataset.collector.ai.ai_tagger import AiTagger
from anki_addons_dataset.collector.ai.cached_ai_provider import CachedAiProvider
from anki_addons_dataset.common.data_types import AddonTitle, AddonDescription, GithubReadme, AiTag
from anki_addons_dataset.common.working_dir import SnapshotDir
from anki_addons_dataset.config.app_config import AppConfig

log: Logger = logging.getLogger(__name__)


def test_tag(ai_provider: AiProvider, integration_config: AppConfig, snapshot_dir: SnapshotDir) -> None:
    cache_file: Path = snapshot_dir.get_ai_cache_file()
    cached_ai_provider: CachedAiProvider = CachedAiProvider(ai_provider, cache_file)
    assert cached_ai_provider.get_cache_stats().hit_count == 0
    assert cached_ai_provider.get_cache_stats().miss_count == 0

    ai_tagger: AiTagger = AiTagger(cached_ai_provider, integration_config.ai.readme_max_chars)
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
    tags: Optional[list[AiTag]] = ai_tagger.tag(title, description, readme)
    log.info(f"Tags: {tags}")
    log.info(f"Cache hits: {cached_ai_provider.get_cache_stats().hit_count}")
    log.info(f"Cache misses: {cached_ai_provider.get_cache_stats().miss_count}")
    assert tags is not None
