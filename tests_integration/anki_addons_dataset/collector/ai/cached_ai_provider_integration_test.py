from pathlib import Path
from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText
from anki_addons_dataset.collector.ai.cached_ai_provider import CachedAiProvider
from anki_addons_dataset.common.working_dir import SnapshotDir


def test_response(ai_provider: AiProvider, snapshot_dir: SnapshotDir) -> None:
    cache_file: Path = snapshot_dir.get_ai_cache_file()
    cached_ai_provider: CachedAiProvider = CachedAiProvider(ai_provider, cache_file)
    prompt: AiPrompt = AiPrompt("What is the capital of France?")

    answer: Optional[AiResponseText] = cached_ai_provider.response(prompt)
    print(answer)
    assert answer is not None
    assert cached_ai_provider.get_cache_stats().miss_count == 1

    assert cached_ai_provider.response(prompt) == answer
    assert cached_ai_provider.get_cache_stats().hit_count == 1
    print(cache_file.read_text())
