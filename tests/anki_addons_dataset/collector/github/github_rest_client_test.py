from pathlib import Path
from typing import Optional
from unittest.mock import patch

import pytest
from requests import Response
from requests.exceptions import HTTPError

from anki_addons_dataset.collector.github.github_rest_client import GithubRestClient


def __make_client(tmp_path: Path) -> GithubRestClient:
    token_dir: Path = tmp_path / ".github"
    token_dir.mkdir(parents=True)
    (token_dir / "token.txt").write_text("secret-token\n")
    with patch.object(Path, "home", return_value=tmp_path):
        return GithubRestClient(offline=False)


def __response(status_code: int, limit_remaining: Optional[str] = None) -> Response:
    response: Response = Response()
    response.status_code = status_code
    if limit_remaining is not None:
        response.headers["x-ratelimit-remaining"] = limit_remaining
    return response


def test_adds_if_none_match_when_etag_given(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               return_value=__response(304)) as mock_request:
        client.get_from_url("https://api.github.com/repos/a/b", etag='W/"abc"')
    headers = mock_request.call_args.kwargs["headers"]
    assert headers["If-None-Match"] == 'W/"abc"'
    assert headers["Authorization"] == "Bearer secret-token"


def test_no_if_none_match_without_etag_and_shared_headers_untouched(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               return_value=__response(200)) as mock_request:
        client.get_from_url("https://api.github.com/repos/a/b", etag='W/"abc"')
        client.get_from_url("https://api.github.com/repos/a/b")  # no etag after an etag call
    second_headers = mock_request.call_args_list[1].kwargs["headers"]
    assert "If-None-Match" not in second_headers  # shared headers were not mutated by the first call


def test_missing_token_file(tmp_path: Path):
    with patch.object(Path, "home", return_value=tmp_path):
        with pytest.raises(FileNotFoundError, match="Missing GitHub token file"):
            GithubRestClient(offline=False)


def test_empty_token_file(tmp_path: Path):
    token_dir: Path = tmp_path / ".github"
    token_dir.mkdir(parents=True)
    (token_dir / "token.txt").write_text("  \n")
    with patch.object(Path, "home", return_value=tmp_path):
        with pytest.raises(ValueError, match="Empty GitHub token file"):
            GithubRestClient(offline=False)


def test_verify_token_returns_remaining_quota(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               return_value=__response(200, "4999")) as mock_request:
        assert client.verify_token() == 4999
    assert mock_request.call_args.args[1] == "https://api.github.com/rate_limit"
    assert mock_request.call_args.kwargs["headers"]["Authorization"] == "Bearer secret-token"


def test_verify_token_raises_permission_error_when_rejected(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               return_value=__response(401)):
        with pytest.raises(PermissionError, match="GitHub rejected the token"):
            client.verify_token()


def test_verify_token_raises_on_server_error(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               return_value=__response(500)):
        with pytest.raises(HTTPError):
            client.verify_token()
