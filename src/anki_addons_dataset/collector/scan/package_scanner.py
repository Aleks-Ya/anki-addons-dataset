import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Optional

from anki_addons_dataset.collector.scan.clamav_scanner import ClamavScanner, ClamavVersion
from anki_addons_dataset.collector.scan.scan_cache_index import ScanCacheIndex
from anki_addons_dataset.common.data_types import PackageScan, SnapshotDate
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


class PackageScanner:
    __batch_size: int = 10
    __pool_size: int = os.cpu_count() or 1
    __progress_step: int = 500

    def __init__(self, clamav_scanner: ClamavScanner, shared_index: ScanCacheIndex):
        self.__clamav_scanner: ClamavScanner = clamav_scanner
        self.__shared_index: ScanCacheIndex = shared_index
        self.__write_lock: threading.Lock = threading.Lock()

    def scan(self, snapshot_dirs: list[SnapshotDir]) -> None:
        version: ClamavVersion = self.__clamav_scanner.version()
        log.info(f"ClamAV {version.engine}, signature database {version.database_version} "
                 f"from {version.database_date}")
        for snapshot_dir in snapshot_dirs:
            self.__scan_snapshot(snapshot_dir, version)

    def __scan_snapshot(self, snapshot_dir: SnapshotDir, version: ClamavVersion) -> None:
        snapshot_date: SnapshotDate = snapshot_dir.snapshot_dir_to_snapshot_date()
        log.info(f"===== Scan packages of snapshot {snapshot_date} =====")
        cache_file: Path = snapshot_dir.get_scan_cache_file()
        own_scans: dict[str, PackageScan] = ScanCacheIndex.read(cache_file)
        reused: dict[str, PackageScan] = {}
        to_scan: dict[str, Path] = {}
        for package_file in sorted(snapshot_dir.get_package_dir().glob("*/*.ankiaddon")):
            if self.__is_current(own_scans.get(package_file.name), version):
                continue
            shared_scan: Optional[PackageScan] = self.__shared_index.get(package_file.name)
            if shared_scan is not None and self.__is_current(shared_scan, version):
                reused[package_file.name] = shared_scan
            else:
                to_scan.setdefault(package_file.name, package_file)
        if reused:
            ScanCacheIndex.append(cache_file, reused, datetime.now())
        log.info(f"Packages already scanned with this database: {len(own_scans) + len(reused)} "
                 f"(copied from other snapshots: {len(reused)}), to scan: {len(to_scan)}")
        files: list[Path] = list(to_scan.values())
        batches: list[list[Path]] = [files[start:start + PackageScanner.__batch_size]
                                     for start in range(0, len(files), PackageScanner.__batch_size)]
        scanned_count: int = 0
        hit_count: int = 0
        with ThreadPoolExecutor(max_workers=PackageScanner.__pool_size, thread_name_prefix="scan") as executor:
            for scans in executor.map(lambda batch: self.__scan_batch(batch, version, cache_file), batches):
                previous_count: int = scanned_count
                scanned_count += len(scans)
                hit_count += sum(1 for scan in scans.values() if scan.signatures)
                if scanned_count // PackageScanner.__progress_step > previous_count // PackageScanner.__progress_step:
                    log.info(f"Scanned {scanned_count} of {len(files)} packages")
        log.info(f"Scanned {scanned_count} packages, {hit_count} with a signature match")
        log.info(f"===== Scanned packages of snapshot {snapshot_date} =====\n")

    def __scan_batch(self, batch: list[Path], version: ClamavVersion, cache_file: Path) -> dict[str, PackageScan]:
        scans: dict[str, PackageScan] = {
            package_file.name: PackageScan(version.engine, version.database_version, signatures)
            for package_file, signatures in self.__clamav_scanner.scan(batch).items()}
        for package_file in batch:
            signatures: list[str] = scans[package_file.name].signatures
            if signatures:
                log.warning(f"ClamAV signature match in {package_file}: {', '.join(signatures)}")
        with self.__write_lock:
            ScanCacheIndex.append(cache_file, scans, datetime.now())
            for file_name, scan in scans.items():
                self.__shared_index.put(file_name, scan)
        return scans

    @staticmethod
    def __is_current(scan: Optional[PackageScan], version: ClamavVersion) -> bool:
        return scan is not None and scan.database_version >= version.database_version
