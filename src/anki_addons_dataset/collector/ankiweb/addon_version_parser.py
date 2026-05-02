import datetime
import re
from datetime import date
from re import Match
from typing import Optional

from anki_addons_dataset.common.data_types import AddonVersion


class AddonVersionParser:
    __addon_version_re: re.Pattern[str] = re.compile(
        r'^(?P<min>\d+(?:\.\d+)*)'
        r'(?:-(?P<max>\d+(?:\.\d+)*\+?)|(?P<plus>\+))?'
        r' \(Updated (?P<updated>\d{4}-\d{2}-\d{2})\)$'
    )

    @staticmethod
    def extract_addon_version(addon_version_str: str) -> AddonVersion:
        match: Optional[Match[str]] = AddonVersionParser.__addon_version_re.fullmatch(addon_version_str)
        if not match:
            raise ValueError(f"Cannot parse version string: {addon_version_str!r}")
        min_addon_version: str = match.group("min")
        max_addon_version: str = match.group("max")
        if max_addon_version is None and match.group("plus") is not None:
            max_addon_version = "+"
        updated: date = datetime.date.fromisoformat(match.group("updated"))
        return AddonVersion(min_version=min_addon_version, max_version=max_addon_version, updated=updated)
