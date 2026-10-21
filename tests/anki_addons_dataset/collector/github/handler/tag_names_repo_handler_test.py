from pathlib import Path

from anki_addons_dataset.collector.github.handler.tag_names_repo_handler import TagNamesRepoHandler
from anki_addons_dataset.common.data_types import GithubRepo


def test_get_url(tmp_path: Path, github_repo: GithubRepo):
    handler: TagNamesRepoHandler = TagNamesRepoHandler(github_repo, tmp_path / "raw", tmp_path / "stage")
    assert handler.get_url() == "https://api.github.com/repos/John/app/git/matching-refs/tags"


def test_extract_return_value_strips_ref_prefix(tmp_path: Path, github_repo: GithubRepo):
    handler: TagNamesRepoHandler = TagNamesRepoHandler(github_repo, tmp_path / "raw", tmp_path / "stage")
    raw_file: Path = handler.get_raw_file()
    raw_file.parent.mkdir(parents=True)
    raw_file.write_text('[{"ref": "refs/tags/2.1.66"}, {"ref": "refs/tags/25.09.2"}]')
    assert raw_file.name == "tags.json"
    assert handler.extract_return_value() == ["2.1.66", "25.09.2"]
