import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from zipfile import BadZipFile, LargeZipFile, ZipFile, ZipInfo

from magika import Magika
from magika.types import MagikaResult

from anki_addons_dataset.collector.package.package_client import PackageError
from anki_addons_dataset.common.data_types import LanguageName


@dataclass(frozen=True)
class PackageAnalysis:
    manifest_json: Optional[str]
    config_json: Optional[str]
    file_count: int
    uncompressed_bytes: int
    python_file_count: int
    python_lines: int
    files: list[str]
    language_bytes: dict[LanguageName, int]


class PackageAnalyzer:
    __encrypted_flag: int = 0x1
    __max_read_bytes: int = 5_000_000
    __max_metadata_bytes: int = 64_000

    def __init__(self) -> None:
        self.__magika: Magika = Magika()
        self.__analyses: dict[str, PackageAnalysis] = {}

    def analyze(self, package_file: Path) -> PackageAnalysis:
        analysis: Optional[PackageAnalysis] = self.__analyses.get(package_file.name)
        if analysis is None:
            try:
                analysis = self.__analyze(package_file)
            except (BadZipFile, LargeZipFile, zlib.error, EOFError, OSError, NotImplementedError) as e:
                raise PackageError(f"{type(e).__name__}: {e}") from e
            self.__analyses[package_file.name] = analysis
        return analysis

    def __analyze(self, package_file: Path) -> PackageAnalysis:
        with ZipFile(package_file) as archive:
            entries: dict[str, ZipInfo] = {entry.filename: entry for entry in archive.infolist()
                                           if not entry.is_dir() and not self.__is_macos_junk(entry.filename)}
            if any(entry.flag_bits & PackageAnalyzer.__encrypted_flag for entry in entries.values()):
                raise PackageError("The package holds encrypted files")
            python_file_count: int = 0
            python_lines: int = 0
            language_bytes: dict[LanguageName, int] = {}
            for name, entry in entries.items():
                content: Optional[bytes] = archive.read(entry) \
                    if 0 < entry.file_size <= PackageAnalyzer.__max_read_bytes else None
                if name.endswith(".py"):
                    python_file_count += 1
                    python_lines += len(content.splitlines()) if content is not None else 0
                language: Optional[LanguageName] = self.__detect_language(content) if content is not None else None
                if language is not None:
                    language_bytes[language] = language_bytes.get(language, 0) + entry.file_size
            return PackageAnalysis(
                self.__read_metadata(archive, entries.get("manifest.json")),
                self.__read_metadata(archive, entries.get("config.json")),
                len(entries),
                sum(entry.file_size for entry in entries.values()),
                python_file_count,
                python_lines,
                sorted(entries),
                dict(sorted(language_bytes.items(), key=lambda item: (-item[1], item[0]))))

    def __detect_language(self, content: bytes) -> Optional[LanguageName]:
        result: MagikaResult = self.__magika.identify_bytes(content)
        if not result.ok or result.output.group != "code":
            return None
        return LanguageName(str(result.output.label))

    @staticmethod
    def __is_macos_junk(name: str) -> bool:
        return name.startswith("__MACOSX/") or name.rsplit("/", 1)[-1].startswith("._")

    @staticmethod
    def __read_metadata(archive: ZipFile, entry: Optional[ZipInfo]) -> Optional[str]:
        if entry is None or entry.file_size > PackageAnalyzer.__max_metadata_bytes:
            return None
        return archive.read(entry).decode("utf-8-sig", errors="replace")
