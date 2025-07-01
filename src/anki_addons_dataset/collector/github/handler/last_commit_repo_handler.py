from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from requests import Response

from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler
from anki_addons_dataset.common.json_helper import JsonHelper


class LastCommitRepoHandler(RepoHandler):

    def get_raw_filename(self) -> str:
        return "last-commit"

    def get_stage_filename(self) -> str:
        return "last-commit"

    def get_url(self) -> str:
        return f"https://api.github.com/repos/{self._repo.user}/{self._repo.repo_name}/commits?per_page=1"

    def extract_return_value_from_dict(self, content_obj: list[dict[str, Any]]) -> Optional[datetime]:
        if len(content_obj) == 0:
            return None
        json_dict: dict[str, Any] = content_obj[0]
        date: Optional[str] = json_dict.get("commit", {}).get("committer", {}).get("date")
        date_obj: Optional[datetime] = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ") if date else None
        return date_obj

    def status_409(self, response: Response) -> None:
        print(f"Repo is empty: {self.get_url()}")
        raw_file: Path = self.get_raw_file()
        JsonHelper.write_dict_to_file({}, raw_file)

    def prepare_stage_dict(self, return_value: Any) -> dict[str, Any]:
        pass

    def write_stage(self, return_value: Any) -> None:
        raw_file: Path = self.get_raw_file()
        self.get_stage_file().write_text(raw_file.read_text())
