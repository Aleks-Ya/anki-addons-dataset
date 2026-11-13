import copy
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from logging import Logger
from pathlib import Path
from typing import Optional

from anki_addons_dataset.collector.package.package_analyzer import PackageAnalysis, PackageAnalyzer
from anki_addons_dataset.collector.package.package_cache_index import PackageKey
from anki_addons_dataset.collector.package.package_client import PackageError
from anki_addons_dataset.collector.scan.scan_cache_index import ScanCacheIndex
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AddonPackage, AddonPackages, \
    AnkiPointVersion, PackageScan
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


class PackageEnricher:
    __pool_size: int = os.cpu_count() or 1

    def __init__(self, snapshot_dir: SnapshotDir, package_analyzer: PackageAnalyzer) -> None:
        self.__package_dir: Path = snapshot_dir.get_package_dir()
        self.__package_analyzer: PackageAnalyzer = package_analyzer
        self.__scans: dict[str, PackageScan] = ScanCacheIndex.read(snapshot_dir.get_scan_cache_file())

    def enrich(self, addon_infos: AddonInfos) -> AddonInfos:
        with ThreadPoolExecutor(max_workers=self.__pool_size, thread_name_prefix="package") as executor:
            analyzed: list[list[Optional[AddonPackage]]] = list(executor.map(self.__analyze_addon, addon_infos))
        failed_count: int = sum(1 for packages in analyzed for package in packages if package is None)
        enriched: list[AddonInfo] = []
        for addon_info, packages in zip(addon_infos, analyzed, strict=True):
            branches: list[AddonPackage] = [package for package in packages if package is not None]
            enriched.append(copy.replace(addon_info, package=AddonPackages(branches) if branches else None))
        log.info(f"Addons with a package: {sum(1 for addon_info in enriched if addon_info.package is not None)}")
        if failed_count:
            log.warning(f"{failed_count} packages cannot be read")
        unscanned_count: int = sum(1 for addon_info in enriched if addon_info.package is not None
                                   for branch in addon_info.package.branches if branch.scan is None)
        if unscanned_count:
            log.warning(f"{unscanned_count} packages have no ClamAV scan. Run the 'scan' operation to scan them.")
        return AddonInfos(enriched)

    def __analyze_addon(self, addon_info: AddonInfo) -> list[Optional[AddonPackage]]:
        return [self.__analyze(key, file) for key, file in self.__newest_files(addon_info.header.id)]

    def __newest_files(self, addon_id: AddonId) -> list[tuple[PackageKey, Path]]:
        newest: dict[AnkiPointVersion, tuple[PackageKey, Path]] = {}
        for file in sorted((self.__package_dir / str(addon_id)).glob("*.ankiaddon")):
            key: Optional[PackageKey] = PackageKey.from_file(file)
            if key is None:
                continue
            current: Optional[tuple[PackageKey, Path]] = newest.get(key.min_point_version)
            if current is None or key.updated >= current[0].updated:
                newest[key.min_point_version] = (key, file)
        return [newest[min_point_version] for min_point_version in sorted(newest)]

    def __analyze(self, key: PackageKey, file: Path) -> Optional[AddonPackage]:
        try:
            analysis: PackageAnalysis = self.__package_analyzer.analyze(file)
        except PackageError as e:
            log.warning(f"Cannot read package {file}: {e}")
            return None
        return AddonPackage(file.name, key.min_point_version, key.updated, file.stat().st_size, analysis.manifest_json,
                            analysis.config_json, analysis.file_count, analysis.uncompressed_bytes,
                            analysis.python_file_count, analysis.python_lines, analysis.files,
                            analysis.language_bytes, self.__scans.get(file.name))
