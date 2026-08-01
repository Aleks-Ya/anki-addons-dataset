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
        except ValueError:  # json.JSONDecodeError subclasses ValueError
            log.info("Could not parse manifest.json")
            return None
        if not isinstance(data, dict):
            return None
        # Per the Anki spec, `package` (the add-on folder name) and `name` are required strings.
        # A manifest with a non-string value in a string field (e.g. an object) is malformed and
        # cannot be represented/exported, so ignore the whole manifest rather than coercing fields.
        package: Any = data.get("package")
        if not isinstance(package, str):
            log.info("Ignoring malformed manifest.json: 'package' is not a string")
            return None
        name: Any = data.get("name")
        homepage: Any = data.get("homepage")
        if not ManifestParser.__str_or_absent(name) or not ManifestParser.__str_or_absent(homepage):
            log.info("Ignoring malformed manifest.json: a string field has a non-string value")
            return None
        conflicts: Any = data.get("conflicts", [])
        return AddonManifest(
            package=package,
            name=name,
            conflicts=[str(conflict) for conflict in conflicts] if isinstance(conflicts, list) else [],
            min_point_version=ManifestParser.__as_int(data.get("min_point_version")),
            max_point_version=ManifestParser.__as_int(data.get("max_point_version")),
            homepage=homepage,
            mod=ManifestParser.__as_int(data.get("mod")),
        )

    @staticmethod
    def __as_int(value: Any) -> Optional[int]:
        return value if isinstance(value, int) else None

    @staticmethod
    def __str_or_absent(value: Any) -> bool:
        return value is None or isinstance(value, str)
