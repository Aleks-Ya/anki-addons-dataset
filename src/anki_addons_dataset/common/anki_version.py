import logging
import re
from logging import Logger
from typing import Optional

from anki_addons_dataset.common.data_types import AnkiPointVersion, AnkiVersionKind

log: Logger = logging.getLogger(__name__)


class AnkiVersionCodec:
    __version_re: re.Pattern[str] = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")
    __header_re: re.Pattern[str] = re.compile(r"<=(?P<hard>\d+\.\d+(?:\.\d+)?)|(?P<tested>\d+\.\d+(?:\.\d+)?)~")

    @staticmethod
    def to_point(version: str) -> AnkiPointVersion:
        match: Optional[re.Match[str]] = AnkiVersionCodec.__version_re.match(version)
        if not match:
            raise ValueError(f"Cannot parse Anki version: {version!r}")
        major: int = int(match.group(1))
        minor: int = int(match.group(2))
        patch: int = int(match.group(3)) if match.group(3) else 0
        if major == 2:
            return AnkiPointVersion(patch)
        return AnkiPointVersion(major * 10_000 + minor * 100 + patch)

    @staticmethod
    def to_str(point: AnkiPointVersion) -> str:
        if point <= 99:
            return f"2.1.{point}"
        year: int = point // 10_000
        month: int = (point // 100) % 100
        patch: int = point % 100
        version: str = f"{year:02}.{month:02}"
        if patch:
            version += f".{patch}"
        return version

    @staticmethod
    def parse_header(header: str) -> tuple[Optional[AnkiPointVersion], AnkiVersionKind]:
        if header == "":
            return None, AnkiVersionKind.UNKNOWN
        match: Optional[re.Match[str]] = AnkiVersionCodec.__header_re.fullmatch(header)
        if match and match.group("hard"):
            return AnkiVersionCodec.to_point(match.group("hard")), AnkiVersionKind.HARD
        if match and match.group("tested"):
            return AnkiVersionCodec.to_point(match.group("tested")), AnkiVersionKind.TESTED
        log.warning(f"Cannot parse Anki version of the addons page: {header!r}")
        return None, AnkiVersionKind.UNKNOWN

    @staticmethod
    def from_manifest_max(max_point_version: Optional[int]) -> tuple[Optional[AnkiPointVersion], AnkiVersionKind]:
        if not max_point_version:
            return None, AnkiVersionKind.UNKNOWN
        if max_point_version < 0:
            return AnkiPointVersion(-max_point_version), AnkiVersionKind.HARD
        return AnkiPointVersion(max_point_version), AnkiVersionKind.TESTED
