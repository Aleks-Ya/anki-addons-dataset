import json
from pathlib import Path

from anki_addons_dataset.collector.ai.ai_cache_index import AiCacheIndex
from anki_addons_dataset.collector.ai.ai_provider import AiResponseText


def write_cache(cache_file: Path, records: list[dict[str, str]]) -> Path:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    return cache_file


def record(key: str, response: str) -> dict[str, str]:
    return {"key": key, "model": "stub-model", "response": response, "created_at": "2026-09-27T12:00:00"}


def test_load_takes_the_answer_from_the_last_file(tmp_path: Path) -> None:
    older: Path = write_cache(tmp_path / "older.jsonl", [record("a", "old answer"), record("b", "only in older")])
    newer: Path = write_cache(tmp_path / "newer.jsonl", [record("a", "new answer")])

    index: AiCacheIndex = AiCacheIndex.load([older, newer])

    assert index.get("a") == "new answer"
    assert index.get("b") == "only in older"
    assert index.size() == 2


def test_load_skips_a_missing_file(tmp_path: Path) -> None:
    existing: Path = write_cache(tmp_path / "existing.jsonl", [record("a", "answer")])

    index: AiCacheIndex = AiCacheIndex.load([tmp_path / "missing.jsonl", existing])

    assert index.get("a") == "answer"
    assert index.size() == 1


def test_load_of_no_files_is_empty(tmp_path: Path) -> None:
    index: AiCacheIndex = AiCacheIndex.load([])

    assert index.size() == 0
    assert index.get("a") is None


def test_truncated_line_is_skipped(tmp_path: Path) -> None:
    cache_file: Path = write_cache(tmp_path / "cache.jsonl", [record("a", "answer")])
    with cache_file.open("a", encoding="utf-8") as file:
        file.write('{"key": "b", "resp')

    index: AiCacheIndex = AiCacheIndex.load([cache_file])

    assert index.get("a") == "answer"
    assert index.get("b") is None


def test_put_is_visible_to_get(tmp_path: Path) -> None:
    index: AiCacheIndex = AiCacheIndex()

    index.put("a", AiResponseText("answer"))

    assert index.get("a") == "answer"
    assert index.size() == 1
