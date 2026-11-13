from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from anki_addons_dataset.collector.scan.clamav_scanner import ClamavScanner, ClamavVersion
from anki_addons_dataset.collector.scan.package_scanner import PackageScanner
from anki_addons_dataset.collector.scan.scan_cache_index import ScanCacheIndex
from anki_addons_dataset.common.data_types import PackageScan, SnapshotDate
from anki_addons_dataset.common.working_dir import SnapshotDir, WorkingDir

__VERSION: ClamavVersion = ClamavVersion("1.5.4", 28181, datetime(2026, 11, 12, 13, 27, 14))
__SCANNED_AT: datetime = datetime(2026, 11, 12, 14, 0, 0)


def __snapshot_dir(working_dir: WorkingDir, snapshot_date: str) -> SnapshotDir:
    return working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat(snapshot_date)))


def __add_package(snapshot_dir: SnapshotDir, addon_id: int, file_name: str) -> Path:
    package_file: Path = snapshot_dir.get_package_dir() / str(addon_id) / file_name
    package_file.parent.mkdir(parents=True, exist_ok=True)
    package_file.write_bytes(b"zip")
    return package_file


def __clamav_scanner(infected: frozenset[str] = frozenset()) -> Mock:
    clamav_scanner: Mock = Mock(spec=ClamavScanner)
    clamav_scanner.version.return_value = __VERSION
    clamav_scanner.scan.side_effect = lambda files: {
        file: ["Eicar-Test-Signature"] if file.name in infected else [] for file in files}
    return clamav_scanner


def __scanned_names(clamav_scanner: Mock) -> list[str]:
    return sorted(file.name for scan_call in clamav_scanner.scan.call_args_list for file in scan_call.args[0])


def test_scan_writes_every_package_to_the_snapshot_cache(working_dir: WorkingDir):
    snapshot_dir: SnapshotDir = __snapshot_dir(working_dir, "2026-11-01")
    __add_package(snapshot_dir, 100, "45-2026-01-15-aaaaaaaaaaaa.ankiaddon")
    __add_package(snapshot_dir, 200, "45-2026-01-15-bbbbbbbbbbbb.ankiaddon")
    clamav_scanner: Mock = __clamav_scanner(frozenset({"45-2026-01-15-bbbbbbbbbbbb.ankiaddon"}))

    PackageScanner(clamav_scanner, ScanCacheIndex()).scan([snapshot_dir])

    assert ScanCacheIndex.read(snapshot_dir.get_scan_cache_file()) == {
        "45-2026-01-15-aaaaaaaaaaaa.ankiaddon": PackageScan("1.5.4", 28181, []),
        "45-2026-01-15-bbbbbbbbbbbb.ankiaddon": PackageScan("1.5.4", 28181, ["Eicar-Test-Signature"])}


def test_scan_logs_a_signature_match(working_dir: WorkingDir, caplog: pytest.LogCaptureFixture):
    snapshot_dir: SnapshotDir = __snapshot_dir(working_dir, "2026-11-01")
    package_file: Path = __add_package(snapshot_dir, 100, "45-2026-01-15-aaaaaaaaaaaa.ankiaddon")

    PackageScanner(__clamav_scanner(frozenset({package_file.name})), ScanCacheIndex()).scan([snapshot_dir])

    assert f"ClamAV signature match in {package_file}: Eicar-Test-Signature" in caplog.text
    assert "Scanned 1 packages, 1 with a signature match" in caplog.text


def test_scan_skips_packages_scanned_with_the_current_database(working_dir: WorkingDir):
    snapshot_dir: SnapshotDir = __snapshot_dir(working_dir, "2026-11-01")
    __add_package(snapshot_dir, 100, "45-2026-01-15-aaaaaaaaaaaa.ankiaddon")
    __add_package(snapshot_dir, 200, "45-2026-01-15-bbbbbbbbbbbb.ankiaddon")
    ScanCacheIndex.append(snapshot_dir.get_scan_cache_file(),
                          {"45-2026-01-15-aaaaaaaaaaaa.ankiaddon": PackageScan("1.5.4", 28181, [])}, __SCANNED_AT)
    clamav_scanner: Mock = __clamav_scanner()

    PackageScanner(clamav_scanner, ScanCacheIndex()).scan([snapshot_dir])

    assert __scanned_names(clamav_scanner) == ["45-2026-01-15-bbbbbbbbbbbb.ankiaddon"]


def test_scan_rescans_packages_scanned_with_an_older_database(working_dir: WorkingDir):
    snapshot_dir: SnapshotDir = __snapshot_dir(working_dir, "2026-11-01")
    __add_package(snapshot_dir, 100, "45-2026-01-15-aaaaaaaaaaaa.ankiaddon")
    ScanCacheIndex.append(snapshot_dir.get_scan_cache_file(),
                          {"45-2026-01-15-aaaaaaaaaaaa.ankiaddon": PackageScan("1.5.4", 28180, [])}, __SCANNED_AT)
    clamav_scanner: Mock = __clamav_scanner(frozenset({"45-2026-01-15-aaaaaaaaaaaa.ankiaddon"}))

    PackageScanner(clamav_scanner, ScanCacheIndex()).scan([snapshot_dir])

    assert ScanCacheIndex.read(snapshot_dir.get_scan_cache_file()) == {
        "45-2026-01-15-aaaaaaaaaaaa.ankiaddon": PackageScan("1.5.4", 28181, ["Eicar-Test-Signature"])}


def test_scan_copies_a_result_from_another_snapshot(working_dir: WorkingDir):
    old_snapshot_dir: SnapshotDir = __snapshot_dir(working_dir, "2026-10-01")
    new_snapshot_dir: SnapshotDir = __snapshot_dir(working_dir, "2026-11-01")
    __add_package(new_snapshot_dir, 100, "45-2026-01-15-aaaaaaaaaaaa.ankiaddon")
    ScanCacheIndex.append(old_snapshot_dir.get_scan_cache_file(),
                          {"45-2026-01-15-aaaaaaaaaaaa.ankiaddon": PackageScan("1.5.4", 28181, [])}, __SCANNED_AT)
    shared_index: ScanCacheIndex = ScanCacheIndex.load([old_snapshot_dir.get_scan_cache_file()])
    clamav_scanner: Mock = __clamav_scanner()

    PackageScanner(clamav_scanner, shared_index).scan([new_snapshot_dir])

    clamav_scanner.scan.assert_not_called()
    assert ScanCacheIndex.read(new_snapshot_dir.get_scan_cache_file()) == {
        "45-2026-01-15-aaaaaaaaaaaa.ankiaddon": PackageScan("1.5.4", 28181, [])}


def test_scan_scans_a_package_shared_by_snapshots_once(working_dir: WorkingDir):
    old_snapshot_dir: SnapshotDir = __snapshot_dir(working_dir, "2026-10-01")
    new_snapshot_dir: SnapshotDir = __snapshot_dir(working_dir, "2026-11-01")
    __add_package(old_snapshot_dir, 100, "45-2026-01-15-aaaaaaaaaaaa.ankiaddon")
    __add_package(new_snapshot_dir, 100, "45-2026-01-15-aaaaaaaaaaaa.ankiaddon")
    __add_package(new_snapshot_dir, 200, "45-2026-01-15-aaaaaaaaaaaa.ankiaddon")
    clamav_scanner: Mock = __clamav_scanner()

    PackageScanner(clamav_scanner, ScanCacheIndex()).scan([old_snapshot_dir, new_snapshot_dir])

    assert __scanned_names(clamav_scanner) == ["45-2026-01-15-aaaaaaaaaaaa.ankiaddon"]
    assert ScanCacheIndex.read(new_snapshot_dir.get_scan_cache_file()) == {
        "45-2026-01-15-aaaaaaaaaaaa.ankiaddon": PackageScan("1.5.4", 28181, [])}


def test_scan_of_a_snapshot_without_packages(working_dir: WorkingDir):
    snapshot_dir: SnapshotDir = __snapshot_dir(working_dir, "2026-11-01")
    clamav_scanner: Mock = __clamav_scanner()

    PackageScanner(clamav_scanner, ScanCacheIndex()).scan([snapshot_dir])

    clamav_scanner.scan.assert_not_called()
    assert not snapshot_dir.get_scan_cache_file().exists()
