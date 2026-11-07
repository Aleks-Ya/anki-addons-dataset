import hashlib
import logging
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor
from logging import Logger
from pathlib import Path
from threading import Lock
from typing import Optional

from requests import RequestException

from anki_addons_dataset.collector.package.package_cache_index import CachedPackage, PackageCacheIndex, PackageKey
from anki_addons_dataset.collector.package.package_client import PackageClient, PackageError, PackageLocation
from anki_addons_dataset.collector.package.package_list import PackageList
from anki_addons_dataset.common.data_types import AddonBranch, AddonHeader, AddonId, AddonInfo, AddonInfos, \
    AnkiPointVersion
from anki_addons_dataset.common.file_links import FileLinks
from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


class PackageCollector:
    __pool_size: int = 2
    __hash_length: int = 12

    def __init__(self, snapshot_dir: SnapshotDir, package_client: PackageClient,
                 cache_index: PackageCacheIndex) -> None:
        self.__snapshot_dir: SnapshotDir = snapshot_dir
        self.__package_dir: Path = snapshot_dir.get_package_dir()
        self.__package_client: PackageClient = package_client
        self.__cache_index: PackageCacheIndex = cache_index
        self.__counts_lock: Lock = Lock()
        self.__downloaded_count: int = 0
        self.__reused_count: int = 0
        self.__failed_count: int = 0

    def collect(self, addon_infos: AddonInfos) -> None:
        log.info(f"Collecting packages of {len(addon_infos)} addons, {self.__cache_index.size()} already cached")
        self.__package_dir.mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor(max_workers=self.__pool_size, thread_name_prefix="package") as executor:
            list(executor.map(self.__collect_addon, addon_infos))
        PackageList.write(self.__snapshot_dir)
        log.info(f"Packages downloaded: {self.__downloaded_count}, reused: {self.__reused_count}, "
                 f"failed: {self.__failed_count}")
        if self.__failed_count:
            log.warning(f"{self.__failed_count} packages are missing. Re-run the 'download' operation to retry them.")

    def __collect_addon(self, addon_info: AddonInfo) -> None:
        addon_id: AddonId = addon_info.header.id
        branches: list[Optional[AddonBranch]] = list(addon_info.page.branches or []) or [None]
        for branch in branches:
            try:
                if branch is None:
                    self.__collect_without_branch(addon_info.header)
                else:
                    self.__collect_branch(addon_id, branch)
            except (PackageError, RequestException, OSError) as e:
                log.warning(f"Cannot collect package of addon {addon_id} (branch {branch}): {e}")
                self.__count_failed()

    def __collect_branch(self, addon_id: AddonId, branch: AddonBranch) -> None:
        if branch.min_point_version is None:
            raise PackageError("The branch has no minimum point version")
        key: PackageKey = PackageKey(addon_id, branch.min_point_version, branch.updated)
        if self.__is_available(key):
            return
        for point_version in self.__point_versions(branch):
            location: Optional[PackageLocation] = self.__package_client.locate(addon_id, point_version)
            if location is not None and location.min_point_version == key.min_point_version:
                self.__download(key, location)
                return
        raise PackageError("AnkiWeb has no package for the branch")

    def __collect_without_branch(self, addon_header: AddonHeader) -> None:
        addon_id: AddonId = addon_header.id
        for point_version in self.__distinct([addon_header.anki_point_version, AnkiPointVersion(0)]):
            location: Optional[PackageLocation] = self.__package_client.locate(addon_id, point_version)
            if location is not None:
                key: PackageKey = PackageKey(addon_id, location.min_point_version, location.uploaded)
                if not self.__is_available(key):
                    self.__download(key, location)
                return
        raise PackageError("AnkiWeb has no package for the addon")

    @staticmethod
    def __point_versions(branch: AddonBranch) -> list[AnkiPointVersion]:
        return PackageCollector.__distinct([branch.min_point_version, branch.max_point_version])

    @staticmethod
    def __distinct(candidates: list[Optional[AnkiPointVersion]]) -> list[AnkiPointVersion]:
        return list(dict.fromkeys(candidate for candidate in candidates if candidate is not None))

    def __is_available(self, key: PackageKey) -> bool:
        addon_dir: Path = self.__package_dir / str(key.addon_id)
        if next(addon_dir.glob(f"{key.file_prefix()}*.ankiaddon"), None) is not None:
            return True
        cached: Optional[CachedPackage] = self.__cache_index.latest(key)
        if cached is None or cached.snapshot_date <= key.updated:
            return False
        FileLinks.link_or_copy(cached.file, addon_dir / cached.file.name)
        with self.__counts_lock:
            self.__reused_count += 1
        return True

    def __download(self, key: PackageKey, location: PackageLocation) -> None:
        addon_dir: Path = self.__package_dir / str(key.addon_id)
        addon_dir.mkdir(parents=True, exist_ok=True)
        part_file: Path = addon_dir / f"{key.file_prefix()}part"
        try:
            if not self.__package_client.download(location, part_file):
                raise PackageError("AnkiWeb did not serve the package")
            if not zipfile.is_zipfile(part_file):
                raise PackageError("The package is not a valid zip")
            file_name: str = key.file_name(self.__content_hash(part_file))
            existing: Optional[Path] = self.__cache_index.find(key.addon_id, file_name)
            if existing is not None:
                FileLinks.link_or_copy(existing, addon_dir / file_name)
            else:
                os.replace(part_file, addon_dir / file_name)
        finally:
            part_file.unlink(missing_ok=True)
        with self.__counts_lock:
            self.__downloaded_count += 1
        log.info(f"Downloaded package of addon {key.addon_id}: {file_name}")

    @staticmethod
    def __content_hash(file: Path) -> str:
        with file.open("rb") as content:
            return hashlib.file_digest(content, "sha256").hexdigest()[:PackageCollector.__hash_length]

    def __count_failed(self) -> None:
        with self.__counts_lock:
            self.__failed_count += 1
