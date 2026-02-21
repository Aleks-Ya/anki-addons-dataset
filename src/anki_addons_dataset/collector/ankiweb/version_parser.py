import datetime
import re
from datetime import date
from re import Match
from typing import Optional

from anki_addons_dataset.common.data_types import Version


class VersionParser:

    @staticmethod
    def extract_version(version_str: str) -> Version:
        pattern: str = r'([\d.]+)-?([\d.+]+)? \(Updated (\d{4}-\d{2}-\d{2})\)'
        match: Optional[Match[str]] = re.search(pattern, version_str)
        if match:
            group_count: int = len(match.groups())
            if group_count == 3:
                min_version: str = match.group(1)
                max_version: str = match.group(2)
                update_date_str: str = match.group(3)
            elif group_count == 2:
                min_version: str = match.group(1)
                max_version: str = ""
                update_date_str: str = match.group(2)
            else:
                raise RuntimeError(f'Cannot parse version: "{version_str}"')
            update_date: date = datetime.datetime.fromisoformat(update_date_str).date()
            version_info: Version = Version(min_version, max_version, update_date)
            return version_info
        else:
            raise RuntimeError(f'Cannot parse version: "{version_str}"')
