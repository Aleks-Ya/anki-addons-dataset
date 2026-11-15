import re
import zlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from zipfile import BadZipFile, LargeZipFile, ZipFile, ZipInfo

from magika import Magika
from magika.types import MagikaResult

from anki_addons_dataset.collector.package.package_client import PackageError
from anki_addons_dataset.collector.package.package_language_names import PackageLanguageNames
from anki_addons_dataset.collector.license.license_classifier import LicenseClassifier
from anki_addons_dataset.common.data_types import LanguageName, PackageLicenseSource, SpdxLicense


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
    license: Optional[SpdxLicense]
    license_source: Optional[PackageLicenseSource]
    license_file: Optional[str]


class PackageAnalyzer:
    __encrypted_flag: int = 0x1
    __max_read_bytes: int = 5_000_000
    __max_metadata_bytes: int = 64_000
    __license_file_name: re.Pattern[str] = re.compile(r"^(licen[cs]e|copying|unlicense)(\.(txt|md|rst))?$",
                                                      re.IGNORECASE)

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
            entries: dict[str, ZipInfo] = self.__entries(archive)
            python_file_count: int = 0
            python_lines: int = 0
            language_bytes: dict[LanguageName, int] = {}
            license_file: Optional[str] = next(
                (name for name in sorted(entries) if PackageAnalyzer.__license_file_name.match(name)), None)
            file_license: Optional[SpdxLicense] = None
            header_licenses: list[SpdxLicense] = []
            for name, entry in entries.items():
                content: bytes = self.__read_content(archive, entry)
                if name.endswith(".py"):
                    python_file_count += 1
                    python_lines += len(content.splitlines())
                if not content:
                    continue
                if name == license_file:
                    file_license = LicenseClassifier.from_text(content.decode("utf-8", errors="replace"))
                header_licenses.extend(self.__header_licenses(name, content))
                language: Optional[LanguageName] = self.__detect_language(content)
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
                dict(sorted(language_bytes.items(), key=lambda item: (-item[1], item[0]))),
                *PackageAnalyzer.__license(file_license, header_licenses), license_file)

    @staticmethod
    def __entries(archive: ZipFile) -> dict[str, ZipInfo]:
        entries: dict[str, ZipInfo] = {entry.filename: entry for entry in archive.infolist()
                                       if not entry.is_dir() and not PackageAnalyzer.__is_macos_junk(entry.filename)}
        if any(entry.flag_bits & PackageAnalyzer.__encrypted_flag for entry in entries.values()):
            raise PackageError("The package holds encrypted files")
        return entries

    @staticmethod
    def __read_content(archive: ZipFile, entry: ZipInfo) -> bytes:
        return archive.read(entry) if 0 < entry.file_size <= PackageAnalyzer.__max_read_bytes else b""

    @staticmethod
    def __header_licenses(name: str, content: bytes) -> list[SpdxLicense]:
        if not name.endswith(".py") or "/" in name:
            return []
        header_license: Optional[SpdxLicense] = LicenseClassifier.from_header(
            content.decode("utf-8", errors="replace"))
        return [header_license] if header_license is not None else []

    def __detect_language(self, content: bytes) -> Optional[LanguageName]:
        result: MagikaResult = self.__magika.identify_bytes(content)
        if not result.ok or result.output.group != "code":
            return None
        return PackageLanguageNames.linguist_name(str(result.output.label))

    @staticmethod
    def __license(file_license: Optional[SpdxLicense], header_licenses: list[SpdxLicense]
                  ) -> tuple[Optional[SpdxLicense], Optional[PackageLicenseSource]]:
        if file_license is not None:
            return file_license, PackageLicenseSource.FILE
        ranked: list[tuple[SpdxLicense, int]] = Counter(header_licenses).most_common(2)
        if not ranked or len(ranked) == 2 and ranked[0][1] == ranked[1][1]:
            return None, None
        return ranked[0][0], PackageLicenseSource.HEADER

    @staticmethod
    def __is_macos_junk(name: str) -> bool:
        return name.startswith("__MACOSX/") or name.rsplit("/", 1)[-1].startswith("._")

    @staticmethod
    def __read_metadata(archive: ZipFile, entry: Optional[ZipInfo]) -> Optional[str]:
        if entry is None or entry.file_size > PackageAnalyzer.__max_metadata_bytes:
            return None
        return archive.read(entry).decode("utf-8-sig", errors="replace")
