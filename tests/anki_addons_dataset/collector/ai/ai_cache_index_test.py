import json
from pathlib import Path
from typing import Any, Optional

from anki_addons_dataset.collector.ai.ai_cache_index import AiCacheEntry, AiCacheIndex
from anki_addons_dataset.collector.ai.ai_provider import AiResponseText


def write_cache(cache_file: Path, records: list[dict[str, Any]]) -> Path:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    return cache_file


def record(key: str, response: str) -> dict[str, Any]:
    return {"key": key, "model": "stub-model", "response": response, "created_at": "2026-09-27T12:00:00"}


def error_record(key: str, error: str, retryable: bool) -> dict[str, Any]:
    return {"key": key, "model": "stub-model", "error": error, "retryable": retryable,
            "created_at": "2026-09-27T12:00:00"}


def response_of(index: AiCacheIndex, key: str) -> Optional[AiResponseText]:
    entry: Optional[AiCacheEntry] = index.get(key)
    return entry.response if entry else None


def test_load_takes_the_answer_from_the_last_file(tmp_path: Path) -> None:
    older: Path = write_cache(tmp_path / "older.jsonl", [record("a", "old answer"), record("b", "only in older")])
    newer: Path = write_cache(tmp_path / "newer.jsonl", [record("a", "new answer")])

    index: AiCacheIndex = AiCacheIndex.load([older, newer])

    assert response_of(index, "a") == "new answer"
    assert response_of(index, "b") == "only in older"
    assert index.size() == 2


def test_load_skips_a_missing_file(tmp_path: Path) -> None:
    existing: Path = write_cache(tmp_path / "existing.jsonl", [record("a", "answer")])

    index: AiCacheIndex = AiCacheIndex.load([tmp_path / "missing.jsonl", existing])

    assert response_of(index, "a") == "answer"
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

    assert response_of(index, "a") == "answer"
    assert index.get("b") is None


def test_put_is_visible_to_get(tmp_path: Path) -> None:
    index: AiCacheIndex = AiCacheIndex()

    index.put("a", AiCacheEntry(response=AiResponseText("answer")))

    assert response_of(index, "a") == "answer"
    assert index.size() == 1


def test_a_retryable_error_is_not_indexed(tmp_path: Path) -> None:
    cache_file: Path = write_cache(tmp_path / "cache.jsonl", [error_record("a", "timeout", True)])

    index: AiCacheIndex = AiCacheIndex.load([cache_file])

    assert index.get("a") is None
    assert index.size() == 0


def test_a_non_retryable_error_is_indexed(tmp_path: Path) -> None:
    cache_file: Path = write_cache(tmp_path / "cache.jsonl", [error_record("a", "prompt too long", False)])

    index: AiCacheIndex = AiCacheIndex.load([cache_file])

    assert index.get("a") == AiCacheEntry(error="prompt too long")
    assert index.size() == 1


def test_a_later_answer_replaces_an_error(tmp_path: Path) -> None:
    cache_file: Path = write_cache(tmp_path / "cache.jsonl",
                                   [error_record("a", "prompt too long", False), record("a", "answer")])

    index: AiCacheIndex = AiCacheIndex.load([cache_file])

    assert response_of(index, "a") == "answer"


def test_a_retryable_error_keeps_a_known_answer(tmp_path: Path) -> None:
    cache_file: Path = write_cache(tmp_path / "cache.jsonl",
                                   [record("a", "answer"), error_record("a", "timeout", True)])

    index: AiCacheIndex = AiCacheIndex.load([cache_file])

    assert response_of(index, "a") == "answer"
