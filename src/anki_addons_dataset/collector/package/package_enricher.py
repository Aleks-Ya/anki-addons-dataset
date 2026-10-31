import copy
import logging
from logging import Logger
from pathlib import Path
from typing import Optional

from anki_addons_dataset.collector.package.package_analyzer import PackageAnalysis, PackageAnalyzer
from anki_addons_dataset.collector.package.package_cache_index import PackageKey
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AddonPackage, AddonPackages, \
    AnkiPointVersion
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


class PackageEnricher:
    def __init__(self, snapshot_dir: SnapshotDir, package_analyzer: PackageAnalyzer) -> None:
        self.__package_dir: Path = snapshot_dir.get_package_dir()
        self.__package_analyzer: PackageAnalyzer = package_analyzer

    def enrich(self, addon_infos: AddonInfos) -> AddonInfos:
        failed_count: int = 0
        enriched: list[AddonInfo] = []
        for addon_info in addon_infos:
            branches: list[AddonPackage] = []
            for key, file in self.__newest_files(addon_info.header.id):
                package: Optional[AddonPackage] = self.__analyze(key, file)
                if package is None:
                    failed_count += 1
                else:
                    branches.append(package)
            enriched.append(copy.replace(addon_info, package=AddonPackages(branches) if branches else None))
        log.info(f"Addons with a package: {sum(1 for addon_info in enriched if addon_info.package is not None)}")
        if failed_count:
            log.warning(f"{failed_count} packages cannot be read")
        return AddonInfos(enriched)

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
        except Exception as e:
            log.warning(f"Cannot read package {file}: {e}")
            return None
        return AddonPackage(file.name, key.min_point_version, key.updated, file.stat().st_size, analysis.manifest_json,
                            analysis.config_json, analysis.file_count, analysis.uncompressed_bytes,
                            analysis.python_file_count, analysis.python_lines, analysis.files)
