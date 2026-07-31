import json
from typing import Any, Optional
import logging
from logging import Logger

from anki_addons_dataset.common.data_types import AddonManifest

log: Logger = logging.getLogger(__name__)


class ManifestParser:
    """Parses an Anki addon `manifest.json` body into an AddonManifest (best-effort; None on malformed JSON)."""

    @staticmethod
    def parse(content: Optional[str]) -> Optional[AddonManifest]:
        if not content:
            return None
        try:
            data: dict[str, Any] = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            log.info("Could not parse manifest.json")
            return None
        if not isinstance(data, dict):
            return None
        conflicts: Any = data.get("conflicts", [])
        return AddonManifest(
            package=data.get("package"),
            name=data.get("name"),
            conflicts=[str(conflict) for conflict in conflicts] if isinstance(conflicts, list) else [],
            min_point_version=ManifestParser.__as_int(data.get("min_point_version")),
            max_point_version=ManifestParser.__as_int(data.get("max_point_version")),
            homepage=data.get("homepage"),
            mod=ManifestParser.__as_int(data.get("mod")),
        )

    @staticmethod
    def __as_int(value: Any) -> Optional[int]:
        return value if isinstance(value, int) else None
