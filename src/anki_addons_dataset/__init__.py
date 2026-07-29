"""Anki Addons Dataset package.

Exposes ``__version__`` read verbatim from ``version.txt`` (the single source of truth,
kept in sync by ``bump-my-version``). The value is already PEP 440-compliant: development
builds use the ``.dev0`` suffix (e.g. ``1.3.0.dev0``) and releases drop it (``1.3.0``).
"""

from pathlib import Path

__version__: str = (Path(__file__).parent / "version.txt").read_text().strip()
