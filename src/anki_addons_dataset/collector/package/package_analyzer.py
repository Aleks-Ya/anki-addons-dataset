from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from zipfile import ZipFile, ZipInfo


@dataclass(frozen=True)
class PackageAnalysis:
    manifest_json: Optional[str]
    config_json: Optional[str]
    file_count: int
    uncompressed_bytes: int
    python_file_count: int
    python_lines: int
    files: list[str]


class PackageAnalyzer:
    __max_python_bytes: int = 5_000_000
    __max_metadata_bytes: int = 64_000

    def analyze(self, package_file: Path) -> PackageAnalysis:
        with ZipFile(package_file) as archive:
            entries: dict[str, ZipInfo] = {entry.filename: entry for entry in archive.infolist()
                                           if not entry.is_dir() and not self.__is_macos_junk(entry.filename)}
            python_entries: list[ZipInfo] = [entry for name, entry in entries.items() if name.endswith(".py")]
            return PackageAnalysis(
                self.__read_metadata(archive, entries.get("manifest.json")),
                self.__read_metadata(archive, entries.get("config.json")),
                len(entries),
                sum(entry.file_size for entry in entries.values()),
                len(python_entries),
                sum(self.__count_lines(archive, entry) for entry in python_entries),
                sorted(entries))

    @staticmethod
    def __is_macos_junk(name: str) -> bool:
        return name.startswith("__MACOSX/") or name.rsplit("/", 1)[-1].startswith("._")

    @staticmethod
    def __read_metadata(archive: ZipFile, entry: Optional[ZipInfo]) -> Optional[str]:
        if entry is None or entry.file_size > PackageAnalyzer.__max_metadata_bytes:
            return None
        return archive.read(entry).decode("utf-8-sig", errors="replace")

    @staticmethod
    def __count_lines(archive: ZipFile, entry: ZipInfo) -> int:
        if entry.file_size > PackageAnalyzer.__max_python_bytes:
            return 0
        return len(archive.read(entry).splitlines())
