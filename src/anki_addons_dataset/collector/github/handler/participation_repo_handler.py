from pathlib import Path
from typing import Any, Optional

from requests import Response

from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler
from anki_addons_dataset.common.json_helper import JsonHelper


class ParticipationRepoHandler(RepoHandler):

    def _get_raw_filename(self) -> str:
        return "participation"

    def _get_stage_filename(self) -> str:
        return "weekly-commits"

    def get_url(self) -> str:
        return f"https://api.github.com/repos/{self._repo.user}/{self._repo.repo_name}/stats/participation"

    def status_204(self, response: Response) -> None:
        raw_file: Path = self.get_raw_file()
        JsonHelper.write_dict_to_file({}, raw_file)

    def _extract_return_value_from_dict(self, content_obj: Any) -> Optional[list[int]]:
        if not isinstance(content_obj, dict) or not isinstance(content_obj.get("all"), list):
            return None
        return [int(count) for count in content_obj["all"]]

    def _prepare_stage_dict(self, return_value: Optional[list[int]]) -> dict[str, Any]:
        return {"weekly_commits": return_value}
