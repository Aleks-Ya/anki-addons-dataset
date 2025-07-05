from pathlib import Path
from typing import Any

from requests import Response

from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler
from anki_addons_dataset.collector.github.handler.tests_counter import TestsCounter
from anki_addons_dataset.common.json_helper import JsonHelper


class TestsRepoHandler(RepoHandler):

    def _get_raw_filename(self) -> str:
        return "tree"

    def _get_stage_filename(self) -> str:
        return "tests-count"

    def get_url(self) -> str:
        return f"https://api.github.com/repos/{self._repo.user}/{self._repo.repo_name}/git/trees/HEAD?recursive=1"

    def _extract_return_value_from_dict(self, content_obj: dict[str, Any]) -> int:
        is_truncated: bool = content_obj.get("truncated")
        if is_truncated:
            raise RuntimeError(f"Repo tree is truncated: {content_obj['url']}")
        if "tree" not in content_obj:
            return 0
        files: list[str] = [file["path"] for file in content_obj["tree"]]
        return TestsCounter.count_tests(files)

    def _prepare_stage_dict(self, return_value: int) -> dict[str, Any]:
        return {"tests_count": return_value}

    def status_409(self, response: Response) -> None:
        print(f"Repo is empty: {self.get_url()}")
        raw_file: Path = self.get_raw_file()
        JsonHelper.write_dict_to_file({}, raw_file)
