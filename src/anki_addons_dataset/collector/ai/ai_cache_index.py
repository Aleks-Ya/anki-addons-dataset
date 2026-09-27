import json
import logging
import threading
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from typing import Any, Optional

from anki_addons_dataset.collector.ai.ai_provider import AiResponseText

log: Logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AiCacheEntry:
    response: Optional[AiResponseText] = None
    error: Optional[str] = None


class AiCacheIndex:
    key_field: str = "key"
    model_field: str = "model"
    response_field: str = "response"
    error_field: str = "error"
    retryable_field: str = "retryable"
    created_at_field: str = "created_at"

    def __init__(self, entries: Optional[dict[str, AiCacheEntry]] = None):
        self.__entries: dict[str, AiCacheEntry] = entries if entries is not None else {}
        self.__lock: threading.Lock = threading.Lock()

    @staticmethod
    def load(cache_files: list[Path]) -> "AiCacheIndex":
        entries: dict[str, AiCacheEntry] = {}
        for cache_file in cache_files:
            entries.update(AiCacheIndex.read(cache_file))
        return AiCacheIndex(entries)

    @staticmethod
    def read(cache_file: Optional[Path]) -> dict[str, AiCacheEntry]:
        if cache_file is None or not cache_file.exists():
            return {}
        entries: dict[str, AiCacheEntry] = {}
        for line_number, line in enumerate(cache_file.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record: dict[str, Any] = json.loads(line)
                key: str = record[AiCacheIndex.key_field]
                entry: Optional[AiCacheEntry] = AiCacheIndex.__entry(record)
                if entry is not None:
                    entries[key] = entry
            except Exception as e:
                # An interrupted run can leave a truncated line: drop it, the entry gets recomputed.
                log.warning(f"Skipping unreadable cache line {line_number} in {cache_file}: {e}")
        return entries

    @staticmethod
    def __entry(record: dict[str, Any]) -> Optional[AiCacheEntry]:
        if AiCacheIndex.error_field in record:
            if record.get(AiCacheIndex.retryable_field, True):
                return None
            return AiCacheEntry(error=str(record[AiCacheIndex.error_field]))
        return AiCacheEntry(response=AiResponseText(record[AiCacheIndex.response_field]))

    def get(self, key: str) -> Optional[AiCacheEntry]:
        return self.__entries.get(key)

    def put(self, key: str, entry: AiCacheEntry) -> None:
        with self.__lock:
            self.__entries[key] = entry

    def size(self) -> int:
        return len(self.__entries)
