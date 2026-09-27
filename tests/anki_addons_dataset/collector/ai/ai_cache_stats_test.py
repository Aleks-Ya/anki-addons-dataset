from anki_addons_dataset.collector.ai.ai_cache_stats import AiCacheStats


def test_defaults_are_zero() -> None:
    assert AiCacheStats() == AiCacheStats(hit_count=0, miss_count=0)


def test_add_sums_both_fields_without_changing_operands() -> None:
    first: AiCacheStats = AiCacheStats(hit_count=3, miss_count=1)
    second: AiCacheStats = AiCacheStats(hit_count=10, miss_count=4)

    assert first + second == AiCacheStats(hit_count=13, miss_count=5)
    assert first == AiCacheStats(hit_count=3, miss_count=1)
    assert second == AiCacheStats(hit_count=10, miss_count=4)
