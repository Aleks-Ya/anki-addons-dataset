import base64
import binascii
from typing import Any, Optional
import logging
from logging import Logger

from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler

log: Logger = logging.getLogger(__name__)


class ReadmeRepoHandler(RepoHandler):
    """Fetches the repo's README as decoded text via `GET /repos/{u}/{r}/readme` (base64 body)."""

    def _get_raw_filename(self) -> str:
        return "readme"

    def _get_stage_filename(self) -> str:
        return "readme"

    def get_url(self) -> str:
        return f"https://api.github.com/repos/{self._repo.user}/{self._repo.repo_name}/readme"

    def _extract_return_value_from_dict(self, content_obj: dict[str, Any]) -> Optional[str]:
        if content_obj.get("encoding") != "base64" or "content" not in content_obj:
            return None
        try:
            return base64.b64decode(content_obj["content"]).decode("utf-8", errors="replace")
        except (binascii.Error, ValueError):
            log.info(f"Could not decode README for {self._repo.get_id()}")
            return None

    def _prepare_stage_dict(self, return_value: Optional[str]) -> dict[str, Any]:
        return {"readme": return_value}
