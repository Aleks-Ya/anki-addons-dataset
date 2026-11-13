import json
import logging
import threading
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any, Optional

from anki_addons_dataset.common.data_types import PackageScan

log: Logger = logging.getLogger(__name__)


class ScanCacheIndex:
    file_name_field: str = "file_name"
    engine_field: str = "engine"
    database_version_field: str = "database_version"
    signatures_field: str = "signatures"
    scanned_at_field: str = "scanned_at"

    def __init__(self, entries: Optional[dict[str, PackageScan]] = None):
        self.__entries: dict[str, PackageScan] = entries if entries is not None else {}
        self.__lock: threading.Lock = threading.Lock()

    @staticmethod
    def load(cache_files: list[Path]) -> "ScanCacheIndex":
        index: ScanCacheIndex = ScanCacheIndex()
        for cache_file in cache_files:
            for file_name, scan in ScanCacheIndex.read(cache_file).items():
                index.put(file_name, scan)
        return index

    @staticmethod
    def read(cache_file: Path) -> dict[str, PackageScan]:
        if not cache_file.exists():
            return {}
        index: ScanCacheIndex = ScanCacheIndex()
        for line_number, line in enumerate(cache_file.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record: dict[str, Any] = json.loads(line)
                index.put(record[ScanCacheIndex.file_name_field], PackageScan(
                    record[ScanCacheIndex.engine_field], int(record[ScanCacheIndex.database_version_field]),
                    list(record[ScanCacheIndex.signatures_field])))
            except Exception as e:
                # An interrupted run can leave a truncated line: drop it, the package gets scanned again.
                log.warning(f"Skipping unreadable scan cache line {line_number} in {cache_file}: {e}")
        return index.entries()

    @staticmethod
    def append(cache_file: Path, scans: dict[str, PackageScan], scanned_at: datetime) -> None:
        lines: list[str] = [json.dumps({
            ScanCacheIndex.file_name_field: file_name,
            ScanCacheIndex.engine_field: scan.engine,
            ScanCacheIndex.database_version_field: scan.database_version,
            ScanCacheIndex.signatures_field: scan.signatures,
            ScanCacheIndex.scanned_at_field: scanned_at.isoformat(),
        }, ensure_ascii=False) for file_name, scan in scans.items()]
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with cache_file.open("a", encoding="utf-8") as cache:
            cache.writelines(f"{line}\n" for line in lines)

    def get(self, file_name: str) -> Optional[PackageScan]:
        return self.__entries.get(file_name)

    def put(self, file_name: str, scan: PackageScan) -> None:
        with self.__lock:
            current: Optional[PackageScan] = self.__entries.get(file_name)
            if current is None or scan.database_version >= current.database_version:
                self.__entries[file_name] = scan

    def entries(self) -> dict[str, PackageScan]:
        return dict(self.__entries)

    def size(self) -> int:
        return len(self.__entries)
