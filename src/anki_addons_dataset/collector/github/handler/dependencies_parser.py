import re
import tomllib
from typing import Any, Optional
import logging
from logging import Logger

from anki_addons_dataset.common.data_types import DependencyName

log: Logger = logging.getLogger(__name__)

# A dependency name ends at the first version specifier, extra marker, or environment marker.
_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+")


class DependenciesParser:
    """Extracts declared dependency *names* from a `requirements.txt` or `pyproject.toml` body (best-effort)."""

    @staticmethod
    def parse_requirements(content: Optional[str]) -> list[DependencyName]:
        if not content:
            return []
        names: list[DependencyName] = []
        for raw_line in content.splitlines():
            line: str = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue  # skip comments and pip options (-r, -e, --hash, ...)
            name: Optional[DependencyName] = DependenciesParser.__extract_name(line)
            if name is not None:
                names.append(name)
        return DependenciesParser.__dedupe(names)

    @staticmethod
    def parse_pyproject(content: Optional[str]) -> list[DependencyName]:
        if not content:
            return []
        try:
            data: dict[str, Any] = tomllib.loads(content)
        except (tomllib.TOMLDecodeError, ValueError):
            log.info("Could not parse pyproject.toml")
            return []
        names: list[DependencyName] = []
        project_deps: Any = data.get("project", {}).get("dependencies", [])
        if isinstance(project_deps, list):
            names.extend(name for dep in project_deps if (name := DependenciesParser.__extract_name(str(dep))))
        poetry_deps: Any = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        if isinstance(poetry_deps, dict):
            names.extend(DependencyName(dep) for dep in poetry_deps if dep.lower() != "python")
        return DependenciesParser.__dedupe(names)

    @staticmethod
    def __extract_name(spec: str) -> Optional[DependencyName]:
        match = _NAME_RE.match(spec.strip())
        return DependencyName(match.group(0)) if match else None

    @staticmethod
    def __dedupe(names: list[DependencyName]) -> list[DependencyName]:
        return list(dict.fromkeys(names))
