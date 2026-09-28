import hashlib
import json
import logging
import threading
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any, Optional

from anki_addons_dataset.collector.ai.ai_cache_index import AiCacheIndex
from anki_addons_dataset.collector.ai.ai_cache_stats import AiCacheStats
from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText

log: Logger = logging.getLogger(__name__)


class CachedAiProvider(AiProvider):
    def __init__(self, ai_provider: AiProvider, cache_file: Path,
                 shared_index: Optional[AiCacheIndex] = None, offline: bool = False):
        super().__init__(ai_provider.get_model())
        self.__ai_provider: AiProvider = ai_provider
        self.__cache_file: Path = cache_file
        self.__offline: bool = offline
        self.__write_lock: threading.Lock = threading.Lock()
        self.__stats_lock: threading.Lock = threading.Lock()
        self.__shared_index: AiCacheIndex = shared_index if shared_index is not None else AiCacheIndex()
        self.__current: AiCacheIndex = AiCacheIndex.load([cache_file])
        self.__cache_hit_count: int = 0
        self.__cache_miss_count: int = 0

    def response(self, prompt: AiPrompt) -> Optional[AiResponseText]:
        key: str = self.__key(prompt)
        cached: Optional[AiResponseText] = self.__current.get(key)
        if cached is not None:
            log.debug(f"Cache hit for key: {key}")
            self.__count_hit()
            return cached
        shared: Optional[AiResponseText] = self.__shared_index.get(key)
        if shared is not None:
            log.debug(f"Cache hit in another snapshot for key: {key}")
            self.__count_hit()
            # Copied into this snapshot so its 1-raw stays self-contained (see RepoHandler.status_304).
            self.__append(key, shared)
            return shared
        self.__count_miss()
        if self.__offline:
            log.warning(f"Offline mode is enabled. Skip requesting the AI provider for key: {key}")
            return None
        log.debug(f"Cache miss for key: {key}")
        response: Optional[AiResponseText] = self.__ai_provider.response(prompt)
        if response is not None:
            self.__append(key, response)
        return response

    def verify_access(self) -> Optional[str]:
        if self.__offline:
            return None
        return self.__ai_provider.verify_access()

    def __append(self, key: str, response: AiResponseText) -> None:
        record: dict[str, Any] = {
            AiCacheIndex.key_field: key,
            AiCacheIndex.model_field: self.get_model(),
            AiCacheIndex.response_field: response,
            AiCacheIndex.created_at_field: datetime.now().isoformat(),
        }
        line: str = json.dumps(record, ensure_ascii=False)
        with self.__write_lock:
            self.__current.put(key, response)
            self.__shared_index.put(key, response)
            self.__cache_file.parent.mkdir(parents=True, exist_ok=True)
            with self.__cache_file.open("a", encoding="utf-8") as cache_file:
                cache_file.write(f"{line}\n")

    def __count_hit(self) -> None:
        with self.__stats_lock:
            self.__cache_hit_count += 1

    def __count_miss(self) -> None:
        with self.__stats_lock:
            self.__cache_miss_count += 1

    def __key(self, prompt: AiPrompt) -> str:
        payload: str = json.dumps([self.get_model(), prompt])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get_cache_stats(self) -> AiCacheStats:
        with self.__stats_lock:
            return AiCacheStats(self.__cache_hit_count, self.__cache_miss_count)
