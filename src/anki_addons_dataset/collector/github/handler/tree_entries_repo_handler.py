from typing import Any

from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler
from anki_addons_dataset.collector.github.handler.tree_reader import TreeReader


class TreeEntriesRepoHandler(RepoHandler):
    """Returns the repo's file paths from the cached `tree.json` (shared with TestsRepoHandler, no extra call)."""

    def _get_raw_filename(self) -> str:
        return "tree"

    def _get_stage_filename(self) -> str:
        return "tree-entries"

    def get_url(self) -> str:
        return f"https://api.github.com/repos/{self._repo.user}/{self._repo.repo_name}/git/trees/HEAD?recursive=1"

    def _extract_return_value_from_dict(self, content_obj: dict[str, Any]) -> list[str]:
        return TreeReader.extract_file_paths(content_obj)

    def _prepare_stage_dict(self, return_value: list[str]) -> dict[str, Any]:
        return {"file_paths": return_value}

    def get_not_found_return_value(self) -> list[str]:
        return []
