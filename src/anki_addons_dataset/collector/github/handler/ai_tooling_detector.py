import re
from typing import Optional, Pattern

# Fingerprint files that AI coding tools drop into a repo. Basename -> normalized tool slug.
_BASENAME_MARKERS: dict[str, str] = {
    "CLAUDE.md": "claude-code",
    "GEMINI.md": "gemini",
    "AGENTS.md": "agents-md",
    ".cursorrules": "cursor",
    ".windsurfrules": "windsurf",
    ".clinerules": "cline",
    "copilot-instructions.md": "copilot",
}

# Directory a tool creates; matched against any path segment. Segment -> tool slug.
_DIR_MARKERS: dict[str, str] = {
    ".cursor": "cursor",
    ".claude": "claude-code",
    ".windsurf": "windsurf",
    ".continue": "continue",
    ".roo": "cline",
}

# README provenance strings. Each pattern (case-insensitive) maps to a tool slug.
_README_MARKERS: list[tuple[Pattern[str], str]] = [
    (re.compile(r"co-authored-by:\s*claude", re.IGNORECASE), "claude-code"),
    (re.compile(r"generated with (?:\[)?claude code", re.IGNORECASE), "claude-code"),
    (re.compile(r"🤖 generated with", re.IGNORECASE), "claude-code"),
    (re.compile(r"vibe[- ]coded", re.IGNORECASE), "vibe-coded"),
]

# "made with <tool>" README phrasing; the captured tool name is normalized to a slug.
_MADE_WITH: Pattern[str] = re.compile(r"\bmade with (cursor|copilot|v0|bolt\.new|lovable)\b", re.IGNORECASE)
_MADE_WITH_SLUGS: dict[str, str] = {"bolt.new": "bolt"}


class AiToolingDetector:
    """Detects positive evidence that a repo was built with AI coding tools.

    Scans the (already-fetched) repo file tree for tool fingerprint files/dirs and the README text for
    provenance markers. Returns the sorted, de-duplicated tool slugs found. An empty list means no evidence
    was detected -- never that the addon was *not* AI-assisted.
    """

    @staticmethod
    def detect(file_paths: list[str], readme: Optional[str]) -> list[str]:
        markers: set[str] = set()
        for path in file_paths:
            segments: list[str] = path.split("/")
            basename: str = segments[-1]
            if basename in _BASENAME_MARKERS:
                markers.add(_BASENAME_MARKERS[basename])
            if basename.startswith(".aider"):
                markers.add("aider")
            for segment in segments[:-1]:
                if segment in _DIR_MARKERS:
                    markers.add(_DIR_MARKERS[segment])
        if readme:
            for pattern, slug in _README_MARKERS:
                if pattern.search(readme):
                    markers.add(slug)
            for tool in _MADE_WITH.findall(readme):
                markers.add(_MADE_WITH_SLUGS.get(tool.lower(), tool.lower()))
        return sorted(markers)
