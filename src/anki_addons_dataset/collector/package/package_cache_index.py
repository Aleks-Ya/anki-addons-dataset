import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import ClassVar, Optional

from anki_addons_dataset.common.data_types import AddonId, AnkiPointVersion, SnapshotDate
from anki_addons_dataset.common.working_dir import SnapshotDir


@dataclass(frozen=True)
class PackageKey:
    __file_name_pattern: ClassVar[re.Pattern[str]] = re.compile(r"^(\d+)-(\d{4}-\d{2}-\d{2})-[0-9a-f]{12}\.ankiaddon$")

    addon_id: AddonId
    min_point_version: AnkiPointVersion
    updated: date

    @staticmethod
    def from_file(file: Path) -> Optional["PackageKey"]:
        match: Optional[re.Match[str]] = PackageKey.__file_name_pattern.match(file.name)
        if match is None:
            return None
        return PackageKey(AddonId(int(file.parent.name)), AnkiPointVersion(int(match.group(1))),
                          date.fromisoformat(match.group(2)))

    def file_prefix(self) -> str:
        return f"{self.min_point_version}-{self.updated.isoformat()}-"

    def file_name(self, content_hash: str) -> str:
        return f"{self.file_prefix()}{content_hash}.ankiaddon"


@dataclass(frozen=True)
class CachedPackage:
    file: Path
    snapshot_date: SnapshotDate


class PackageCacheIndex:
    def __init__(self, latest: dict[PackageKey, CachedPackage], files: dict[tuple[AddonId, str], Path]) -> None:
        self.__latest: dict[PackageKey, CachedPackage] = latest
        self.__files: dict[tuple[AddonId, str], Path] = files

    @staticmethod
    def load(snapshot_dirs: list[SnapshotDir]) -> "PackageCacheIndex":
        latest: dict[PackageKey, CachedPackage] = {}
        files: dict[tuple[AddonId, str], Path] = {}
        for snapshot_dir in sorted(snapshot_dirs):
            snapshot_date: SnapshotDate = snapshot_dir.snapshot_dir_to_snapshot_date()
            for file in snapshot_dir.get_package_dir().glob("*/*.ankiaddon"):
                key: Optional[PackageKey] = PackageKey.from_file(file)
                if key is None:
                    continue
                latest[key] = CachedPackage(file, snapshot_date)
                files[(key.addon_id, file.name)] = file
        return PackageCacheIndex(latest, files)

    def latest(self, key: PackageKey) -> Optional[CachedPackage]:
        return self.__latest.get(key)

    def find(self, addon_id: AddonId, file_name: str) -> Optional[Path]:
        return self.__files.get((addon_id, file_name))

    def size(self) -> int:
        return len(self.__files)
