import re
from collections.abc import Callable
from typing import Optional

from anki_addons_dataset.common.data_types import SpdxLicense

type LicenseResolver = Callable[[str, re.Match[str]], Optional[SpdxLicense]]


class LicenseClassifier:
    __header_line_count: int = 30
    __version_window: int = 200
    __separators: re.Pattern[str] = re.compile(r"[\s#*]+")
    __spdx_identifier: re.Pattern[str] = re.compile(r"SPDX-License-Identifier:\s*([\w.+-]+)")
    __spdx_suffix: re.Pattern[str] = re.compile(r"(-or-later|-only|\+)$")
    __license_heading: re.Pattern[str] = re.compile(r"^#{1,6}\s*licen[cs]e", re.IGNORECASE | re.MULTILINE)
    __heading: re.Pattern[str] = re.compile(r"^#{1,6}\s", re.MULTILINE)
    __leading_version: re.Pattern[str] = re.compile(r"\W*v?(\d(?:\.\d)?)")
    __worded_version: re.Pattern[str] = re.compile(r"\bversion\W+(\d(?:\.\d)?)")
    __gpl_versions: dict[str, str] = {"2": "GPL-2.0", "2.0": "GPL-2.0", "3": "GPL-3.0", "3.0": "GPL-3.0"}
    __lgpl_versions: dict[str, str] = {"2": "LGPL-2.0", "2.0": "LGPL-2.0", "2.1": "LGPL-2.1", "3": "LGPL-3.0",
                                       "3.0": "LGPL-3.0"}

    @staticmethod
    def from_text(text: str) -> Optional[SpdxLicense]:
        normalized: str = LicenseClassifier.__separators.sub(" ", text).lower()
        matches: list[tuple[re.Match[str], LicenseResolver]] = [
            (match, resolver) for pattern, resolver in LicenseClassifier.__rules
            for match in [pattern.search(normalized)] if match is not None]
        for match, resolver in sorted(matches, key=lambda item: item[0].start()):
            spdx_license: Optional[SpdxLicense] = resolver(normalized, match)
            if spdx_license is not None:
                return spdx_license
        return None

    @staticmethod
    def from_header(source: str) -> Optional[SpdxLicense]:
        header: str = "\n".join(source.splitlines()[:LicenseClassifier.__header_line_count])
        identifier: Optional[re.Match[str]] = LicenseClassifier.__spdx_identifier.search(header)
        if identifier is not None:
            return SpdxLicense(LicenseClassifier.__spdx_suffix.sub("", identifier.group(1)))
        return LicenseClassifier.from_text(header)

    @staticmethod
    def from_readme(readme: str) -> Optional[SpdxLicense]:
        license_heading: Optional[re.Match[str]] = LicenseClassifier.__license_heading.search(readme)
        if license_heading is None:
            return None
        next_heading: Optional[re.Match[str]] = LicenseClassifier.__heading.search(readme, license_heading.end())
        section_end: int = next_heading.start() if next_heading is not None else len(readme)
        return LicenseClassifier.from_text(readme[license_heading.start():section_end])

    @staticmethod
    def __fixed(spdx_license: str) -> LicenseResolver:
        return lambda text, match: SpdxLicense(spdx_license)

    @staticmethod
    def __versioned(versions: dict[str, str]) -> LicenseResolver:
        def resolve(text: str, match: re.Match[str]) -> Optional[SpdxLicense]:
            window: str = text[match.end():match.end() + LicenseClassifier.__version_window]
            version: Optional[re.Match[str]] = LicenseClassifier.__leading_version.match(window) \
                or LicenseClassifier.__worded_version.search(window)
            if version is None:
                return None
            spdx_license: Optional[str] = versions.get(version.group(1))
            return SpdxLicense(spdx_license) if spdx_license is not None else None
        return resolve

    @staticmethod
    def __bsd(text: str, match: re.Match[str]) -> Optional[SpdxLicense]:
        return SpdxLicense("BSD-3-Clause" if "neither the name" in text else "BSD-2-Clause")

    @staticmethod
    def __creative_commons(text: str, match: re.Match[str]) -> Optional[SpdxLicense]:
        terms: str = "".join(f"-{term}" for term, present in (("NC", match.group(1)), ("SA", match.group(2)),
                                                              ("ND", match.group(3))) if present)
        return SpdxLicense(f"CC-BY{terms}-{match.group(4)}")

    __rules: list[tuple[re.Pattern[str], LicenseResolver]] = [
        (re.compile(r"affero general public licen[cs]e|\bagpl"), __fixed("AGPL-3.0")),
        (re.compile(r"(?:lesser|library) general public licen[cs]e|\blgpl"), __versioned(__lgpl_versions)),
        (re.compile(r"general public licen[cs]e|\bgpl"), __versioned(__gpl_versions)),
        (re.compile(r"\bapache licen[cs]e\W+(?:version )?2\.0"), __fixed("Apache-2.0")),
        (re.compile(r"\bmozilla public licen[cs]e\W+(?:version |v)?2\.0"), __fixed("MPL-2.0")),
        (re.compile(r"\bmit licen[cs]e|mit-license|licen[cs]ed?\W+(?:under\W+)?(?:the\W+)?mit\b"
                    r"|permission is hereby granted, free of charge"), __fixed("MIT")),
        (re.compile(r"\bisc licen[cs]e|permission to use, copy, modify, and/or distribute this software"),
         __fixed("ISC")),
        (re.compile(r"\bbsd[ -]3-clause"), __fixed("BSD-3-Clause")),
        (re.compile(r"\bbsd[ -]2-clause"), __fixed("BSD-2-Clause")),
        (re.compile(r"redistribution and use in source and binary forms"), __bsd),
        (re.compile(r"free and unencumbered software released into the public domain|\bthe unlicense\b"),
         __fixed("Unlicense")),
        (re.compile(r"\bcc0\b"), __fixed("CC0-1.0")),
        (re.compile(r"creative commons (?:legal code )?attribution([- ]noncommercial)?([- ]sharealike)?"
                    r"([- ]no ?deriv(?:ative)?s)?\W+(\d\.\d)"), __creative_commons),
        (re.compile(r"do what the fuck you want"), __fixed("WTFPL")),
    ]
