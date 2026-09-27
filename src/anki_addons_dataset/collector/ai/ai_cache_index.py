import json
import logging
import threading
from logging import Logger
from pathlib import Path
from typing import Any, Optional

from anki_addons_dataset.collector.ai.ai_provider import AiResponseText

log: Logger = logging.getLogger(__name__)


class AiCacheIndex:
    key_field: str = "key"
    model_field: str = "model"
    response_field: str = "response"
    created_at_field: str = "created_at"

    def __init__(self, entries: Optional[dict[str, AiResponseText]] = None):
        self.__entries: dict[str, AiResponseText] = entries if entries is not None else {}
        self.__lock: threading.Lock = threading.Lock()

    @staticmethod
    def load(cache_files: list[Path]) -> "AiCacheIndex":
        entries: dict[str, AiResponseText] = {}
        for cache_file in cache_files:
            entries.update(AiCacheIndex.read(cache_file))
        return AiCacheIndex(entries)

    @staticmethod
    def read(cache_file: Optional[Path]) -> dict[str, AiResponseText]:
        if cache_file is None or not cache_file.exists():
            return {}
        entries: dict[str, AiResponseText] = {}
        for line_number, line in enumerate(cache_file.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record: dict[str, Any] = json.loads(line)
                entries[record[AiCacheIndex.key_field]] = AiResponseText(record[AiCacheIndex.response_field])
            except Exception as e:
                # An interrupted run can leave a truncated line: drop it, the entry gets recomputed.
                log.warning(f"Skipping unreadable cache line {line_number} in {cache_file}: {e}")
        return entries

    def get(self, key: str) -> Optional[AiResponseText]:
        return self.__entries.get(key)

    def put(self, key: str, response: AiResponseText) -> None:
        with self.__lock:
            self.__entries[key] = response

    def size(self) -> int:
        return len(self.__entries)
