from typing import Any

from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler


class TagNamesRepoHandler(RepoHandler):
    __ref_prefix: str = "refs/tags/"

    def _get_raw_filename(self) -> str:
        return "tags"

    def _get_stage_filename(self) -> str:
        return "tag-names"

    def get_url(self) -> str:
        return f"https://api.github.com/repos/{self._repo.user}/{self._repo.repo_name}/git/matching-refs/tags"

    def _extract_return_value_from_dict(self, content_obj: Any) -> list[str]:
        if not isinstance(content_obj, list):
            return []
        return [ref["ref"].removeprefix(self.__ref_prefix) for ref in content_obj]

    def _prepare_stage_dict(self, return_value: list[str]) -> dict[str, Any]:
        return {"tag_names": return_value}

    def get_not_found_return_value(self) -> list[str]:
        return []
