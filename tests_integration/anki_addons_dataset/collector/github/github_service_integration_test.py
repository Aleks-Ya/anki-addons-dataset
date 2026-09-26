from datetime import datetime
from pathlib import Path

import pytest

from anki_addons_dataset.collector.github.github_rest_client import GithubRestClient
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.collector.github.handler.repo_info_repo_handler import GithubRepoMeta
from anki_addons_dataset.common.data_types import AddonManifest, DependencyName, GithubRepo, LanguageName
from anki_addons_dataset.common.working_dir import SnapshotDir


@pytest.fixture
def github_service(snapshot_dir: SnapshotDir, github_rest_client: GithubRestClient,
                   github_rate_limit_guard: int) -> GithubService:
    return GithubService(snapshot_dir, github_rest_client)


def test_verify_token(github_rest_client: GithubRestClient) -> None:
    remaining: int = github_rest_client.verify_token()
    assert isinstance(remaining, int)
    assert remaining >= 0


def test_known_repo(github_service: GithubService, snapshot_dir: SnapshotDir,
                    known_github_repo: GithubRepo) -> None:
    assert github_service.get_stars_count(known_github_repo) >= 0

    last_commit: datetime = github_service.get_last_commit(known_github_repo)
    assert last_commit is not None
    assert last_commit < datetime.now()

    languages: dict[LanguageName, int] = github_service.get_languages(known_github_repo)
    assert "Python" in languages
    assert languages["Python"] > 0

    assert github_service.get_action_count(known_github_repo) is not None

    tests_count: int = github_service.get_tests_count(known_github_repo)
    assert tests_count is not None
    assert tests_count > 0

    meta: GithubRepoMeta = github_service.get_repo_info(known_github_repo)
    assert meta.forks is not None
    assert meta.open_issues is not None
    assert meta.size_kb is not None
    assert meta.created_at is not None
    assert meta.archived is False

    readme: str = github_service.get_readme(known_github_repo)
    assert readme
    assert len(readme) > 100

    assert isinstance(github_service.get_ai_tooling_markers(known_github_repo, readme), list)

    repo_raw_dir: Path = (snapshot_dir.get_raw_dir() / "2-github" / known_github_repo.user
                          / known_github_repo.repo_name)
    assert (repo_raw_dir / "info.json").exists()
    assert (repo_raw_dir / "info.etag").exists()


def test_repo_contents(github_service: GithubService, contents_github_repo: GithubRepo) -> None:
    manifest: AddonManifest = github_service.get_manifest(contents_github_repo)
    assert manifest is not None
    assert manifest.name or manifest.package

    dependencies: list[DependencyName] = github_service.get_dependencies(contents_github_repo)
    assert dependencies
    assert dependencies == list(dict.fromkeys(dependencies))


def test_missing_repo(github_service: GithubService, snapshot_dir: SnapshotDir,
                      missing_github_repo: GithubRepo) -> None:
    assert github_service.get_stars_count(missing_github_repo) == 0
    assert github_service.get_last_commit(missing_github_repo) is None
    assert github_service.get_languages(missing_github_repo) == {}
    assert github_service.get_repo_info(missing_github_repo) == GithubRepoMeta()
    assert github_service.get_readme(missing_github_repo) is None
    not_found_marker: Path = (snapshot_dir.get_raw_dir() / "2-github" / missing_github_repo.user
                              / missing_github_repo.repo_name / "NOT_FOUND_404")
    assert not_found_marker.exists()
