from datetime import datetime
from unittest.mock import Mock

from pytest import raises
from requests import Response

from anki_addons_dataset.collector.github.github_rest_client import GithubRestClient
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.common.data_types import GithubRepo, LanguageName


def test_repo_none(github_service: GithubService):
    assert github_service.get_languages(None) is None
    assert github_service.get_stars_count(None) is None
    assert github_service.get_last_commit(None) is None
    assert github_service.get_action_count(None) is None
    assert github_service.get_tests_count(None) is None


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
    with raises(RuntimeError) as ex_info:
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


def __mock_content(content: str, status_code: int = 200) -> Mock:
    response: Response = Response()
    response.status_code = status_code
    response._content = content.encode("utf-8")
    return Mock(return_value=response)
