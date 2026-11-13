from datetime import datetime
from pathlib import Path

import pytest

from anki_addons_dataset.collector.scan.scan_cache_index import ScanCacheIndex
from anki_addons_dataset.common.data_types import PackageScan

__SCANNED_AT: datetime = datetime(2026, 11, 12, 13, 0, 0)


def test_append_and_read(tmp_path: Path):
    cache_file: Path = tmp_path / "6-scan" / "scan-cache.jsonl"
    scans: dict[str, PackageScan] = {"a.ankiaddon": PackageScan("1.5.4", 28181, ["Eicar-Signature"]),
                                     "b.ankiaddon": PackageScan("1.5.4", 28181, [])}

    ScanCacheIndex.append(cache_file, scans, __SCANNED_AT)

    assert ScanCacheIndex.read(cache_file) == scans
    assert '"scanned_at": "2026-11-12T13:00:00"' in cache_file.read_text()


def test_read_a_missing_file(tmp_path: Path):
    assert ScanCacheIndex.read(tmp_path / "scan-cache.jsonl") == {}


def test_read_keeps_the_newest_database_version(tmp_path: Path):
    cache_file: Path = tmp_path / "scan-cache.jsonl"
    ScanCacheIndex.append(cache_file, {"a.ankiaddon": PackageScan("1.5.4", 28182, ["New.Signature"])}, __SCANNED_AT)
    ScanCacheIndex.append(cache_file, {"a.ankiaddon": PackageScan("1.5.4", 28181, [])}, __SCANNED_AT)

    assert ScanCacheIndex.read(cache_file) == {"a.ankiaddon": PackageScan("1.5.4", 28182, ["New.Signature"])}


def test_read_skips_a_truncated_line(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    cache_file: Path = tmp_path / "scan-cache.jsonl"
    ScanCacheIndex.append(cache_file, {"a.ankiaddon": PackageScan("1.5.4", 28181, [])}, __SCANNED_AT)
    with cache_file.open("a", encoding="utf-8") as cache:
        cache.write('{"file_name": "b.ankiaddon", "eng')

    assert ScanCacheIndex.read(cache_file) == {"a.ankiaddon": PackageScan("1.5.4", 28181, [])}
    assert "Skipping unreadable scan cache line 2" in caplog.text


def test_load_merges_snapshots_by_database_version(tmp_path: Path):
    old_file: Path = tmp_path / "old.jsonl"
    new_file: Path = tmp_path / "new.jsonl"
    ScanCacheIndex.append(old_file, {"a.ankiaddon": PackageScan("1.5.4", 28182, ["New.Signature"]),
                                     "b.ankiaddon": PackageScan("1.5.4", 28100, [])}, __SCANNED_AT)
    ScanCacheIndex.append(new_file, {"a.ankiaddon": PackageScan("1.5.4", 28181, [])}, __SCANNED_AT)

    index: ScanCacheIndex = ScanCacheIndex.load([old_file, new_file])

    assert index.size() == 2
    assert index.get("a.ankiaddon") == PackageScan("1.5.4", 28182, ["New.Signature"])
    assert index.get("b.ankiaddon") == PackageScan("1.5.4", 28100, [])
    assert index.get("c.ankiaddon") is None
