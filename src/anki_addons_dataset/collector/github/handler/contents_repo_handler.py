import base64
from pathlib import Path
from typing import Any, Optional
import logging
from logging import Logger

from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler
from anki_addons_dataset.common.data_types import GithubRepo

log: Logger = logging.getLogger(__name__)


class ContentsRepoHandler(RepoHandler):
    """Fetches a single file's decoded text via `GET /repos/{u}/{r}/contents/{path}` (base64 body)."""

    def __init__(self, repo: GithubRepo, path: str, raw_name: str, raw_dir: Path, stage_dir: Path,
                 prev_raw_dir: Optional[Path] = None) -> None:
        super().__init__(repo, raw_dir, stage_dir, prev_raw_dir)
        self.__path: str = path
        self.__raw_name: str = raw_name

    def _get_raw_filename(self) -> str:
        return self.__raw_name

    def _get_stage_filename(self) -> str:
        return self.__raw_name

    def get_url(self) -> str:
        return f"https://api.github.com/repos/{self._repo.user}/{self._repo.repo_name}/contents/{self.__path}"

    def _extract_return_value_from_dict(self, content_obj: dict[str, Any]) -> Optional[str]:
        if content_obj.get("encoding") != "base64" or "content" not in content_obj:
            return None
        try:
            return base64.b64decode(content_obj["content"]).decode("utf-8", errors="replace")
        except ValueError:  # binascii.Error (invalid base64) subclasses ValueError
            log.info(f"Could not decode contents for {self._repo.get_id()}/{self.__path}")
            return None

    def _prepare_stage_dict(self, return_value: Optional[str]) -> dict[str, Any]:
        return {"content": return_value}
