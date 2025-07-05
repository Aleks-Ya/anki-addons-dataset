from typing import Any

from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler
from anki_addons_dataset.common.data_types import LanguageName


class LanguagesRepoHandler(RepoHandler):

    def _get_raw_filename(self) -> str:
        return "languages"

    def _get_stage_filename(self) -> str:
        return "languages"

    def get_url(self) -> str:
        return f"https://api.github.com/repos/{self._repo.user}/{self._repo.repo_name}/languages"

    def _extract_return_value_from_dict(self, content_obj: dict[str, Any]) -> dict[LanguageName, int]:
        return {LanguageName(k): v for k, v in content_obj.items()}

    def _prepare_stage_dict(self, return_value: dict[LanguageName, int]) -> dict[str, Any]:
        return return_value
