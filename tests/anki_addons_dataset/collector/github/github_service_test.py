import base64
from datetime import date, datetime
from typing import Optional
from unittest.mock import Mock

import pytest
from requests import Response

from anki_addons_dataset.collector.github.github_rest_client import GithubRestClient
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.collector.github.handler.repo_info_repo_handler import GithubRepoMeta
from anki_addons_dataset.common.data_types import AddonManifest, DependencyName, GithubRepo, LanguageName, SnapshotDate, \
    SpdxLicense, Topic
from anki_addons_dataset.common.working_dir import SnapshotDir, WorkingDir


def test_get_languages_200(github_service: GithubService, github_rest_client: GithubRestClient,
                           github_repo: GithubRepo):
    content: str = """{"Python":145190,"Shell":1154}"""
    github_rest_client.get_from_url = __mock_content(content)
    exp: dict[LanguageName, int] = {LanguageName("Python"): 145190, LanguageName("Shell"): 1154}
    assert github_service.get_languages(github_repo) == exp
    assert github_service.get_languages(github_repo) == exp  # cached
    github_rest_client.get_from_url.assert_called_once()


def test_get_languages_404(github_service: GithubService, github_rest_client: GithubRestClient,
                           github_repo: GithubRepo):
    github_rest_client.get_from_url = __mock_content("", status_code=404)
    exp: dict[LanguageName, int] = {}
    assert github_service.get_languages(github_repo) == exp
    assert github_service.get_languages(github_repo) == exp  # cached
    github_rest_client.get_from_url.assert_called_once()


def test_get_languages_409(github_service: GithubService, github_rest_client: GithubRestClient,
                           github_repo: GithubRepo):
    github_rest_client.get_from_url = __mock_content("", status_code=409)
    with pytest.raises(RuntimeError) as ex_info:
        github_service.get_languages(github_repo)
    assert "Error status 409 for John/app: " in ex_info.value.args
    github_rest_client.get_from_url.assert_called_once()


def test_stars_count_200(github_service: GithubService, github_rest_client: GithubRestClient, github_repo: GithubRepo):
    content: str = """{"stargazers_count":5}"""
    github_rest_client.get_from_url = __mock_content(content)
    exp: int = 5
    assert github_service.get_stars_count(github_repo) == exp
    assert github_service.get_stars_count(github_repo) == exp  # cached
    github_rest_client.get_from_url.assert_called_once()


def test_get_last_commit_200(github_service: GithubService, github_rest_client: GithubRestClient,
                             github_repo: GithubRepo):
    content: str = """[{"commit":{"committer":{"date":"2023-02-05T19:55:48Z"}}}]"""
    github_rest_client.get_from_url = __mock_content(content)
    exp: datetime = datetime(2023, 2, 5, 19, 55, 48)
    assert github_service.get_last_commit(github_repo) == exp
    assert github_service.get_last_commit(github_repo) == exp  # cached
    github_rest_client.get_from_url.assert_called_once()


def test_get_action_count_200(github_service: GithubService, github_rest_client: GithubRestClient,
                              github_repo: GithubRepo):
    content: str = """{"total_count":7}"""
    github_rest_client.get_from_url = __mock_content(content)
    exp: int = 7
    assert github_service.get_action_count(github_repo) == exp
    assert github_service.get_action_count(github_repo) == exp  # cached
    github_rest_client.get_from_url.assert_called_once()


def test_get_tests_count_200(github_service: GithubService, github_rest_client: GithubRestClient,
                             github_repo: GithubRepo):
    content: str = """{"tree":[{"path":"src/app/service.py"},{"path":"test/app/service_test.py"}],"truncated":false}"""
    github_rest_client.get_from_url = __mock_content(content)
    exp: int = 1
    assert github_service.get_tests_count(github_repo) == exp
    assert github_service.get_tests_count(github_repo) == exp  # cached
    github_rest_client.get_from_url.assert_called_once()


def test_get_repo_info_200(github_service: GithubService, github_rest_client: GithubRestClient,
                           github_repo: GithubRepo):
    content: str = """{"stargazers_count":5,"license":{"spdx_id":"MIT"},"forks_count":4,"open_issues_count":2,
        "size":128,"topics":["anki","flashcards"],"description":"An addon","homepage":"https://example.com",
        "archived":false,"pushed_at":"2023-03-16T10:00:00Z","created_at":"2020-01-01T09:00:00Z"}"""
    github_rest_client.get_from_url = __mock_content(content)
    meta: GithubRepoMeta = github_service.get_repo_info(github_repo)
    assert meta == GithubRepoMeta(license=SpdxLicense("MIT"), forks=4, open_issues=2, size_kb=128,
                                  topics=[Topic("anki"), Topic("flashcards")], repo_description="An addon",
                                  homepage="https://example.com", archived=False,
                                  pushed_at=datetime(2023, 3, 16, 10, 0, 0), created_at=datetime(2020, 1, 1, 9, 0, 0))


def test_get_repo_info_reuses_stars_info_cache(github_service: GithubService, github_rest_client: GithubRestClient,
                                               github_repo: GithubRepo):
    content: str = """{"stargazers_count":5,"license":{"spdx_id":"MIT"}}"""
    github_rest_client.get_from_url = __mock_content(content)
    assert github_service.get_stars_count(github_repo) == 5
    assert github_service.get_repo_info(github_repo).license == SpdxLicense("MIT")  # extracted from cached info.json
    github_rest_client.get_from_url.assert_called_once()  # no extra API call for repo info


def test_get_repo_info_ignores_noassertion_license(github_service: GithubService,
                                                    github_rest_client: GithubRestClient, github_repo: GithubRepo):
    github_rest_client.get_from_url = __mock_content("""{"license":{"spdx_id":"NOASSERTION"}}""")
    assert github_service.get_repo_info(github_repo).license is None


def test_get_readme_200(github_service: GithubService, github_rest_client: GithubRestClient, github_repo: GithubRepo):
    encoded: str = base64.b64encode(b"# NoteSize\nExample").decode("ascii")
    github_rest_client.get_from_url = __mock_content(f'{{"encoding":"base64","content":"{encoded}"}}')
    assert github_service.get_readme(github_repo) == "# NoteSize\nExample"


def test_get_readme_404(github_service: GithubService, github_rest_client: GithubRestClient, github_repo: GithubRepo):
    github_rest_client.get_from_url = __mock_content("", status_code=404)
    assert github_service.get_readme(github_repo) is None


def test_get_manifest(github_service: GithubService, github_rest_client: GithubRestClient, github_repo: GithubRepo):
    manifest_json: str = """{"package":"note_size","name":"Note Size","conflicts":["123"],
        "min_point_version":45,"homepage":"https://example.com","mod":1678900000}"""
    encoded: str = base64.b64encode(manifest_json.encode()).decode("ascii")
    tree: str = """{"tree":[{"path":"README.md"},{"path":"src/note_size/manifest.json"}],"truncated":false}"""
    github_rest_client.get_from_url = __mock_by_url({
        "https://api.github.com/repos/John/app/git/trees/HEAD?recursive=1": tree,
        "https://api.github.com/repos/John/app/contents/src/note_size/manifest.json":
            f'{{"encoding":"base64","content":"{encoded}"}}',
    })
    assert github_service.get_manifest(github_repo) == AddonManifest(
        package="note_size", name="Note Size", conflicts=["123"], min_point_version=45, max_point_version=None,
        homepage="https://example.com", mod=1678900000)


def test_get_manifest_absent(github_service: GithubService, github_rest_client: GithubRestClient,
                             github_repo: GithubRepo):
    github_rest_client.get_from_url = __mock_content("""{"tree":[{"path":"README.md"}],"truncated":false}""")
    assert github_service.get_manifest(github_repo) is None


def test_get_dependencies(github_service: GithubService, github_rest_client: GithubRestClient, github_repo: GithubRepo):
    requirements: str = base64.b64encode(b"requests>=2.0\n# comment\nbeautifulsoup4==4.12\n").decode("ascii")
    tree: str = """{"tree":[{"path":"requirements.txt"}],"truncated":false}"""
    github_rest_client.get_from_url = __mock_by_url({
        "https://api.github.com/repos/John/app/git/trees/HEAD?recursive=1": tree,
        "https://api.github.com/repos/John/app/contents/requirements.txt":
            f'{{"encoding":"base64","content":"{requirements}"}}',
    })
    assert github_service.get_dependencies(github_repo) == [DependencyName("requests"), DependencyName("beautifulsoup4")]


def test_offline_returns_empties_without_downloading(snapshot_dir: SnapshotDir,
                                                     github_rest_client: GithubRestClient, github_repo: GithubRepo):
    github_rest_client.get_from_url = Mock()
    offline_service: GithubService = GithubService(snapshot_dir, github_rest_client, offline=True)

    assert offline_service.get_stars_count(github_repo) == 0
    assert offline_service.get_languages(github_repo) == {}
    assert offline_service.get_last_commit(github_repo) is None
    assert offline_service.get_action_count(github_repo) is None
    assert offline_service.get_tests_count(github_repo) is None
    assert offline_service.get_repo_info(github_repo) == GithubRepoMeta()
    assert offline_service.get_readme(github_repo) is None
    assert offline_service.get_manifest(github_repo) is None
    assert offline_service.get_dependencies(github_repo) == []
    github_rest_client.get_from_url.assert_not_called()


def test_conditional_get_304_copies_previous_snapshot(working_dir: WorkingDir,
                                                       github_rest_client: GithubRestClient, github_repo: GithubRepo):
    prev_snapshot: SnapshotDir = working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat("2025-01-01"))).create()
    curr_snapshot: SnapshotDir = working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat("2025-01-02"))).create()

    # Previous snapshot: a 200 response carrying an ETag persists an .etag sidecar next to the raw file.
    prev_service: GithubService = GithubService(prev_snapshot, github_rest_client)
    github_rest_client.get_from_url = __mock_content("""{"stargazers_count":5}""", etag='W/"abc"')
    assert prev_service.get_stars_count(github_repo) == 5
    etag_file = prev_snapshot.get_raw_dir() / "2-github" / github_repo.user / github_repo.repo_name / "info.etag"
    assert etag_file.read_text() == 'W/"abc"'

    # Current snapshot: the prior ETag is sent, GitHub answers 304, and the value is copied forward.
    curr_service: GithubService = GithubService(curr_snapshot, github_rest_client, prev_snapshot)
    mock_304: Mock = __mock_content("", status_code=304)
    github_rest_client.get_from_url = mock_304
    assert curr_service.get_stars_count(github_repo) == 5
    mock_304.assert_called_once_with("https://api.github.com/repos/John/app", 'W/"abc"')
    curr_raw = curr_snapshot.get_raw_dir() / "2-github" / github_repo.user / github_repo.repo_name / "info.json"
    assert curr_raw.exists()


def __mock_content(content: str, status_code: int = 200, etag: Optional[str] = None) -> Mock:
    response: Response = Response()
    response.status_code = status_code
    response._content = content.encode("utf-8")
    if etag:
        response.headers["ETag"] = etag
    return Mock(return_value=response)


def __mock_by_url(url_to_content: dict[str, str]) -> Mock:
    def side_effect(url: str, _etag: Optional[str] = None) -> Response:
        response: Response = Response()
        if url in url_to_content:
            response.status_code = 200
            response._content = url_to_content[url].encode("utf-8")
        else:
            response.status_code = 404
            response._content = b""
        return response

    return Mock(side_effect=side_effect)
