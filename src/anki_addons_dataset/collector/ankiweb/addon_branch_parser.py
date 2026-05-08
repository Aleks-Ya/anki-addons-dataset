import datetime
import re
from datetime import date
from re import Match
from typing import Optional

from anki_addons_dataset.common.data_types import AddonBranch, AnkiVersion


class AddonBranchParser:
    __addon_branch_re: re.Pattern[str] = re.compile(
        r'^(?P<min>\d+(?:\.\d+)*)'
        r'(?:-(?P<max>\d+(?:\.\d+)*\+?)|(?P<plus>\+))?'
        r' \(Updated (?P<updated>\d{4}-\d{2}-\d{2})\)$'
    )

    @staticmethod
    def extract_addon_branch(addon_branch_str: str) -> AddonBranch:
        match: Optional[Match[str]] = AddonBranchParser.__addon_branch_re.fullmatch(addon_branch_str)
        if not match:
            raise ValueError(f"Cannot parse version string: {addon_branch_str!r}")
        min_addon_version: AnkiVersion = AnkiVersion(match.group("min"))
        max_addon_version: AnkiVersion = AnkiVersion(match.group("max"))
        if max_addon_version is None and match.group("plus") is not None:
            max_addon_version = AnkiVersion("+")
        updated: date = datetime.date.fromisoformat(match.group("updated"))
        return AddonBranch(min_anki_version=min_addon_version, max_anki_version=max_addon_version, updated=updated)
