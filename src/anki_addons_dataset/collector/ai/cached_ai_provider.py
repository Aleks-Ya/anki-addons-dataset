import hashlib
import json
import logging
import threading
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any, Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText

log: Logger = logging.getLogger(__name__)


class CachedAiProvider(AiProvider):
    __key_field: str = "key"
    __model_field: str = "model"
    __response_field: str = "response"
    __created_at_field: str = "created_at"

    def __init__(self, ai_provider: AiProvider, cache_file: Path,
                 prev_cache_file: Optional[Path] = None, offline: bool = False):
        super().__init__(ai_provider.get_model())
        self.__ai_provider: AiProvider = ai_provider
        self.__cache_file: Path = cache_file
        self.__offline: bool = offline
        self.__write_lock: threading.Lock = threading.Lock()
        self.__carried_forward: dict[str, AiResponseText] = self.__read(prev_cache_file)
        self.__current: dict[str, AiResponseText] = self.__read(cache_file)
        self.__cache_hit_count: int = 0
        self.__cache_miss_count: int = 0

    def response(self, prompt: AiPrompt) -> Optional[AiResponseText]:
        key: str = self.__key(prompt)
        cached: Optional[AiResponseText] = self.__current.get(key)
        if cached is not None:
            log.debug(f"Cache hit for key: {key}")
            self.__cache_hit_count += 1
            return cached
        carried_forward: Optional[AiResponseText] = self.__carried_forward.get(key)
        if carried_forward is not None:
            log.debug(f"Cache hit in the previous snapshot for key: {key}")
            self.__cache_hit_count += 1
            # Copied into this snapshot so its 1-raw stays self-contained (see RepoHandler.status_304).
            self.__append(key, carried_forward)
            return carried_forward
        self.__cache_miss_count += 1
        if self.__offline:
            log.warning(f"Offline mode is enabled. Skip requesting the AI provider for key: {key}")
            return None
        log.debug(f"Cache miss for key: {key}")
        response: Optional[AiResponseText] = self.__ai_provider.response(prompt)
        if response is not None:
            self.__append(key, response)
        return response

    def __append(self, key: str, response: AiResponseText) -> None:
        record: dict[str, Any] = {
            CachedAiProvider.__key_field: key,
            CachedAiProvider.__model_field: self.get_model(),
            CachedAiProvider.__response_field: response,
            CachedAiProvider.__created_at_field: datetime.now().isoformat(),
        }
        line: str = json.dumps(record, ensure_ascii=False)
        with self.__write_lock:
            self.__current[key] = response
            self.__cache_file.parent.mkdir(parents=True, exist_ok=True)
            with self.__cache_file.open("a", encoding="utf-8") as cache_file:
                cache_file.write(f"{line}\n")

    @staticmethod
    def __read(cache_file: Optional[Path]) -> dict[str, AiResponseText]:
        if cache_file is None or not cache_file.exists():
            return {}
        entries: dict[str, AiResponseText] = {}
        for line_number, line in enumerate(cache_file.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record: dict[str, Any] = json.loads(line)
                entries[record[CachedAiProvider.__key_field]] = \
                    AiResponseText(record[CachedAiProvider.__response_field])
            except Exception as e:
                # An interrupted run can leave a truncated line: drop it, the entry gets recomputed.
                log.warning(f"Skipping unreadable cache line {line_number} in {cache_file}: {e}")
        return entries

    def __key(self, prompt: AiPrompt) -> str:
        payload: str = json.dumps([self.get_model(), prompt])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get_cache_hit_count(self) -> int:
        return self.__cache_hit_count

    def get_cache_miss_count(self) -> int:
        return self.__cache_miss_count
