from pathlib import Path
from typing import Any, Optional

from requests import Response

from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler
from anki_addons_dataset.common.data_types import GithubContributor
from anki_addons_dataset.common.json_helper import JsonHelper


class ContributorsRepoHandler(RepoHandler):

    def _get_raw_filename(self) -> str:
        return "contributors"

    def _get_stage_filename(self) -> str:
        return "contributors"

    def get_url(self) -> str:
        return f"https://api.github.com/repos/{self._repo.user}/{self._repo.repo_name}/contributors?per_page=100"

    def status_204(self, response: Response) -> None:
        raw_file: Path = self.get_raw_file()
        JsonHelper.write_content_to_file("[]", raw_file)

    def _extract_return_value_from_dict(self, content_obj: Any) -> Optional[list[GithubContributor]]:
        if not isinstance(content_obj, list):
            return None
        return [GithubContributor(contributor["login"], contributor.get("contributions", 0))
                for contributor in content_obj if contributor.get("login")]

    def _prepare_stage_dict(self, return_value: Optional[list[GithubContributor]]) -> dict[str, Any]:
        contributors: Optional[list[dict[str, Any]]] = \
            [{"login": contributor.login, "contributions": contributor.contributions} for contributor in return_value] \
            if return_value is not None else None
        return {"contributors": contributors}
