import json
import threading
from pathlib import Path
from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText
from anki_addons_dataset.collector.ai.cached_ai_provider import CachedAiProvider
from anki_addons_dataset.common.data_types import AiModel


class StubAiProvider(AiProvider):
    def __init__(self, model: AiModel = AiModel("stub-model")):
        super().__init__(model)
        self.call_count: int = 0

    def response(self, prompt: AiPrompt) -> Optional[AiResponseText]:
        self.call_count += 1
        return AiResponseText(f"answer-{self.call_count} to {prompt}")


def read_lines(cache_file: Path) -> list[dict[str, str]]:
    return [json.loads(line) for line in cache_file.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_miss_then_hit(tmp_path: Path) -> None:
    cache_file: Path = tmp_path / "4-ai" / "ai-cache.jsonl"
    stub: StubAiProvider = StubAiProvider()
    provider: CachedAiProvider = CachedAiProvider(stub, cache_file)
    prompt: AiPrompt = AiPrompt("What is the capital of France?")

    assert provider.response(prompt) == "answer-1 to What is the capital of France?"
    assert provider.response(prompt) == "answer-1 to What is the capital of France?"

    assert stub.call_count == 1
    assert provider.get_cache_hit_count() == 1
    assert provider.get_cache_miss_count() == 1
    lines: list[dict[str, str]] = read_lines(cache_file)
    assert len(lines) == 1
    assert lines[0]["model"] == "stub-model"
    assert lines[0]["response"] == "answer-1 to What is the capital of France?"


def test_cache_survives_a_restart(tmp_path: Path) -> None:
    cache_file: Path = tmp_path / "ai-cache.jsonl"
    prompt: AiPrompt = AiPrompt("Question")
    CachedAiProvider(StubAiProvider(), cache_file).response(prompt)

    stub: StubAiProvider = StubAiProvider()
    provider: CachedAiProvider = CachedAiProvider(stub, cache_file)
    assert provider.response(prompt) == "answer-1 to Question"
    assert stub.call_count == 0
    assert len(read_lines(cache_file)) == 1


def test_previous_snapshot_hit_is_carried_forward(tmp_path: Path) -> None:
    prev_cache_file: Path = tmp_path / "prev" / "ai-cache.jsonl"
    cache_file: Path = tmp_path / "current" / "ai-cache.jsonl"
    prompt: AiPrompt = AiPrompt("Question")
    CachedAiProvider(StubAiProvider(), prev_cache_file).response(prompt)

    stub: StubAiProvider = StubAiProvider()
    provider: CachedAiProvider = CachedAiProvider(stub, cache_file, prev_cache_file)
    assert provider.response(prompt) == "answer-1 to Question"

    assert stub.call_count == 0
    assert provider.get_cache_hit_count() == 1
    carried_forward: dict[str, str] = read_lines(cache_file)[0]
    previous: dict[str, str] = read_lines(prev_cache_file)[0]
    assert carried_forward["key"] == previous["key"]
    assert carried_forward["model"] == previous["model"]
    assert carried_forward["response"] == previous["response"]


def test_unused_previous_entries_are_not_carried_forward(tmp_path: Path) -> None:
    prev_cache_file: Path = tmp_path / "prev" / "ai-cache.jsonl"
    cache_file: Path = tmp_path / "current" / "ai-cache.jsonl"
    prev_provider: CachedAiProvider = CachedAiProvider(StubAiProvider(), prev_cache_file)
    prev_provider.response(AiPrompt("Still asked"))
    prev_provider.response(AiPrompt("No longer asked"))

    provider: CachedAiProvider = CachedAiProvider(StubAiProvider(), cache_file, prev_cache_file)
    provider.response(AiPrompt("Still asked"))

    assert len(read_lines(prev_cache_file)) == 2
    assert [line["response"] for line in read_lines(cache_file)] == ["answer-1 to Still asked"]


def test_current_snapshot_shadows_previous_snapshot(tmp_path: Path) -> None:
    prev_cache_file: Path = tmp_path / "prev" / "ai-cache.jsonl"
    cache_file: Path = tmp_path / "current" / "ai-cache.jsonl"
    prompt: AiPrompt = AiPrompt("Question")
    CachedAiProvider(StubAiProvider(), prev_cache_file).response(prompt)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    key: str = read_lines(prev_cache_file)[0]["key"]
    cache_file.write_text(json.dumps({"key": key, "model": "stub-model", "response": "fresh answer",
                                      "created_at": "2026-09-27T12:00:00"}) + "\n", encoding="utf-8")

    stub: StubAiProvider = StubAiProvider()
    provider: CachedAiProvider = CachedAiProvider(stub, cache_file, prev_cache_file)
    assert provider.response(prompt) == "fresh answer"
    assert stub.call_count == 0
    assert len(read_lines(cache_file)) == 1


def test_truncated_line_is_skipped(tmp_path: Path) -> None:
    cache_file: Path = tmp_path / "ai-cache.jsonl"
    prompt: AiPrompt = AiPrompt("Question")
    CachedAiProvider(StubAiProvider(), cache_file).response(prompt)
    with cache_file.open("a", encoding="utf-8") as file:
        file.write('{"key": "abc", "resp')

    stub: StubAiProvider = StubAiProvider()
    provider: CachedAiProvider = CachedAiProvider(stub, cache_file)
    assert provider.response(prompt) == "answer-1 to Question"
    assert provider.response(AiPrompt("New question")) == "answer-1 to New question"
    assert stub.call_count == 1


def test_another_model_is_a_miss(tmp_path: Path) -> None:
    cache_file: Path = tmp_path / "ai-cache.jsonl"
    prompt: AiPrompt = AiPrompt("Question")
    CachedAiProvider(StubAiProvider(AiModel("model-a")), cache_file).response(prompt)

    stub: StubAiProvider = StubAiProvider(AiModel("model-b"))
    provider: CachedAiProvider = CachedAiProvider(stub, cache_file)
    provider.response(prompt)

    assert stub.call_count == 1
    assert provider.get_cache_miss_count() == 1
    assert [line["model"] for line in read_lines(cache_file)] == ["model-a", "model-b"]


def test_offline_miss_returns_none(tmp_path: Path) -> None:
    cache_file: Path = tmp_path / "ai-cache.jsonl"
    stub: StubAiProvider = StubAiProvider()
    provider: CachedAiProvider = CachedAiProvider(stub, cache_file, offline=True)

    assert provider.response(AiPrompt("Question")) is None
    assert stub.call_count == 0
    assert provider.get_cache_miss_count() == 1
    assert not cache_file.exists()


def test_offline_hit_is_served_from_the_cache(tmp_path: Path) -> None:
    cache_file: Path = tmp_path / "ai-cache.jsonl"
    prompt: AiPrompt = AiPrompt("Question")
    CachedAiProvider(StubAiProvider(), cache_file).response(prompt)

    provider: CachedAiProvider = CachedAiProvider(StubAiProvider(), cache_file, offline=True)
    assert provider.response(prompt) == "answer-1 to Question"


def test_concurrent_appends_produce_readable_lines(tmp_path: Path) -> None:
    cache_file: Path = tmp_path / "ai-cache.jsonl"
    provider: CachedAiProvider = CachedAiProvider(StubAiProvider(), cache_file)
    prompts: list[AiPrompt] = [AiPrompt(f"Question {i}") for i in range(50)]

    threads: list[threading.Thread] = [threading.Thread(target=provider.response, args=(prompt,))
                                       for prompt in prompts]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    lines: list[dict[str, str]] = read_lines(cache_file)
    assert len(lines) == 50
    assert len({line["key"] for line in lines}) == 50
