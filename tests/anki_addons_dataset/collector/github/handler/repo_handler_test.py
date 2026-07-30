from pathlib import Path

from anki_addons_dataset.collector.github.handler.stars_repo_handler import StarsRepoHandler
from anki_addons_dataset.common.data_types import GithubRepo


def test_get_prev_etag_requires_both_files(tmp_path: Path, github_repo: GithubRepo):
    prev_raw_dir: Path = tmp_path / "prev"
    handler: StarsRepoHandler = StarsRepoHandler(github_repo, tmp_path / "raw", tmp_path / "stage", prev_raw_dir)
    repo_dir: Path = prev_raw_dir / github_repo.user / github_repo.repo_name
    repo_dir.mkdir(parents=True)

    (repo_dir / "info.etag").write_text('W/"abc"')
    assert handler.get_prev_etag() is None  # raw body missing -> cannot safely copy forward

    (repo_dir / "info.json").write_text("{}")
    assert handler.get_prev_etag() == 'W/"abc"'


def test_get_prev_etag_none_without_prev_dir(tmp_path: Path, github_repo: GithubRepo):
    handler: StarsRepoHandler = StarsRepoHandler(github_repo, tmp_path / "raw", tmp_path / "stage", None)
    assert handler.get_prev_etag() is None
