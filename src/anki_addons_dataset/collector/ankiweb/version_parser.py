import datetime
import re
from datetime import date
from re import Match

from anki_addons_dataset.common.data_types import Version


class VersionParser:
    __version_re: re.Pattern[str] = re.compile(
        r'^(?P<min>\d+(?:\.\d+)*)'
        r'(?:-(?P<max>\d+(?:\.\d+)*\+?)|(?P<plus>\+))?'
        r' \(Updated (?P<updated>\d{4}-\d{2}-\d{2})\)$'
    )

    @staticmethod
    def extract_version(version_str: str) -> Version:
        match: Match[str] = VersionParser.__version_re.fullmatch(version_str)
        if not match:
            raise ValueError(f"Cannot parse version string: {version_str!r}")
        min_version: str = match.group("min")
        max_version: str = match.group("max")
        if max_version is None and match.group("plus") is not None:
            max_version = "+"
        updated: date = datetime.date.fromisoformat(match.group("updated"))
        return Version(min_version=min_version, max_version=max_version, updated=updated)
