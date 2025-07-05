from typing import Any

from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler


class StarsRepoHandler(RepoHandler):

    def _get_raw_filename(self) -> str:
        return "info"

    def _get_stage_filename(self) -> str:
        return "stars-count"

    def get_url(self) -> str:
        return f"https://api.github.com/repos/{self._repo.user}/{self._repo.repo_name}"

    def _extract_return_value_from_dict(self, content_obj: dict[str, Any]) -> int:
        return content_obj["stargazers_count"] if "stargazers_count" in content_obj else 0

    def _prepare_stage_dict(self, return_value: Any) -> dict[str, Any]:
        return {"stars_count": return_value}

    def get_not_found_return_value(self) -> int:
        return 0
