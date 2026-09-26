from pathlib import Path
from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText
from anki_addons_dataset.collector.ai.cached_ai_provider import CachedAiProvider
from anki_addons_dataset.collector.ai.deepseek_ai_provider import DeepSeekAiProvider
from anki_addons_dataset.common.data_types import AiModel


def test_response(tmp_path: Path) -> None:
    endpoint: str = "https://api.deepseek.com"
    api_key: str = Path("/home/aleks/.config/anki-addons-dataset/deepseek-api-key.txt").read_text().strip()
    model: AiModel = AiModel("deepseek-flash")
    deepseek_ai_provider: AiProvider = DeepSeekAiProvider(endpoint, api_key, model)

    cached_ai_provider: CachedAiProvider = CachedAiProvider(deepseek_ai_provider, tmp_path / "ai-cache.jsonl")
    prompt: AiPrompt = AiPrompt("What is the capital of France?")
    answer: Optional[AiResponseText] = cached_ai_provider.response(prompt)
    print(answer)

    print(f"Cache hits: {cached_ai_provider.get_cache_hit_count()}")
    print(f"Cache misses: {cached_ai_provider.get_cache_miss_count()}")
