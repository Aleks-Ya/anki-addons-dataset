from pathlib import Path
from typing import Optional
from unittest.mock import call, patch

import pytest
from requests import Response
from requests.exceptions import ConnectionError as RequestsConnectionError, HTTPError, InvalidURL, Timeout

from anki_addons_dataset.collector.github.github_rest_client import GithubRestClient


def __token_file(tmp_path: Path) -> Path:
    token_dir: Path = tmp_path / ".github"
    token_dir.mkdir(parents=True)
    return token_dir / "token.txt"


def __make_client(tmp_path: Path) -> GithubRestClient:
    token_file: Path = __token_file(tmp_path)
    token_file.write_text("secret-token\n")
    return GithubRestClient(offline=False, token_file=token_file)


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
    token_file: Path = __token_file(tmp_path)
    with pytest.raises(FileNotFoundError, match="Missing GitHub token file"):
        GithubRestClient(offline=False, token_file=token_file)


def test_empty_token_file(tmp_path: Path):
    token_file: Path = __token_file(tmp_path)
    token_file.write_text("  \n")
    with pytest.raises(ValueError, match="Empty GitHub token file"):
        GithubRestClient(offline=False, token_file=token_file)


def test_token_file_path_is_injected_not_assumed(tmp_path: Path):
    token_file: Path = tmp_path / "custom" / "gh.token"
    token_file.parent.mkdir(parents=True)
    token_file.write_text("other-token\n")
    client: GithubRestClient = GithubRestClient(offline=False, token_file=token_file)
    assert client.get_token_file() == token_file
    assert client.read_token() == "other-token"


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


def test_post_graphql_sends_query_and_variables(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               return_value=__response(200)) as mock_request:
        client.post_graphql("query", {"owner": "a", "name": "b"})
    assert mock_request.call_args.args == ("POST", "https://api.github.com/graphql")
    assert mock_request.call_args.kwargs["json"] == {"query": "query", "variables": {"owner": "a", "name": "b"}}
    assert mock_request.call_args.kwargs["headers"]["Authorization"] == "Bearer secret-token"


def test_post_graphql_keeps_its_rate_limit_apart_from_rest(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request") as mock_request:
        mock_request.return_value = __response(200, "4999")
        client.get_from_url("https://api.github.com/repos/a/b")
        mock_request.return_value = __response(200, "0")
        client.post_graphql("query", {})
        with patch("anki_addons_dataset.collector.github.github_rate_limit.time.sleep") as sleep:
            mock_request.return_value = __response(200, "4998")
            client.get_from_url("https://api.github.com/repos/a/b")
    sleep.assert_not_called()


def __exhausted_response() -> Response:
    response: Response = __response(200, "0")
    response.headers["x-ratelimit-reset"] = "4102444800"
    return response


def test_actions_response_does_not_hide_exhausted_rest_limit(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request") as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.sleep") as sleep:
        mock_request.return_value = __exhausted_response()
        client.get_from_url("https://api.github.com/repos/a/b/languages")
        mock_request.return_value = __response(200, "4609")
        client.get_from_url("https://api.github.com/repos/a/b/actions/workflows")
        sleep.assert_not_called()
        client.get_from_url("https://api.github.com/repos/a/b/readme")
    sleep.assert_called_once()


def test_exhausted_actions_limit_does_not_block_rest(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request") as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.sleep") as sleep:
        mock_request.return_value = __exhausted_response()
        client.get_from_url("https://api.github.com/repos/a/b/actions/workflows")
        mock_request.return_value = __response(200, "4999")
        client.get_from_url("https://api.github.com/repos/a/b/readme")
    sleep.assert_not_called()


def test_repo_named_actions_uses_rest_rate_limit(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request") as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.sleep") as sleep:
        mock_request.return_value = __exhausted_response()
        client.get_from_url("https://api.github.com/repos/a/actions/languages")
        mock_request.return_value = __response(200, "4999")
        client.get_from_url("https://api.github.com/repos/a/b/readme")
    sleep.assert_called_once()


def test_retries_after_rate_limited_response(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    limited: Response = __response(403, "0")
    limited.headers["retry-after"] = "30"
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               side_effect=[limited, __response(200, "4999")]) as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.sleep") as sleep:
        response: Response = client.get_from_url("https://api.github.com/repos/a/b")
    assert response.status_code == 200
    assert mock_request.call_count == 2
    sleep.assert_called_once_with(30)


def test_resend_waits_for_reset_of_exhausted_quota(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    limited: Response = __response(403, "0")
    limited.headers["retry-after"] = "30"
    limited.headers["x-ratelimit-reset"] = "4102444800"
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               side_effect=[limited, __response(200, "4999")]) as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.time", return_value=4102444700.0), \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.sleep") as sleep:
        response: Response = client.get_from_url("https://api.github.com/repos/a/b")
    assert response.status_code == 200
    assert mock_request.call_count == 2
    assert sleep.call_args_list == [call(30), call(100)]


def test_returns_rate_limited_response_when_retries_run_out(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    limited: Response = __response(403)
    limited.headers["retry-after"] = "30"
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               return_value=limited) as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.sleep") as sleep:
        response: Response = client.get_from_url("https://api.github.com/repos/a/b")
    assert response.status_code == 403
    assert mock_request.call_count == 4
    assert sleep.call_count == 3


def test_does_not_retry_forbidden_response(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               return_value=__response(403, "4999")) as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.sleep") as sleep:
        response: Response = client.get_from_url("https://api.github.com/repos/a/b")
    assert response.status_code == 403
    assert mock_request.call_count == 1
    sleep.assert_not_called()


def test_post_graphql_retries_after_rate_limited_response(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    limited: Response = __response(429)
    limited.headers["retry-after"] = "5"
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               side_effect=[limited, __response(200)]) as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.sleep") as sleep:
        response: Response = client.post_graphql("query", {})
    assert response.status_code == 200
    assert mock_request.call_args.kwargs["json"] == {"query": "query", "variables": {}}
    sleep.assert_called_once_with(5)


def __graphql_response(content: bytes, limit_remaining: Optional[str] = None) -> Response:
    response: Response = __response(200, limit_remaining)
    response._content = content
    return response


__graphql_limited_content: bytes = b'{"errors": [{"type": "RATE_LIMITED", "message": "API rate limit exceeded"}]}'


def test_post_graphql_retries_after_limited_ok_response(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    limited: Response = __graphql_response(__graphql_limited_content, "0")
    limited.headers["x-ratelimit-reset"] = "4102444800"
    success: Response = __graphql_response(b'{"data": {"repository": {"name": "b"}}}', "4999")
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               side_effect=[limited, success]) as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.time", return_value=4102444700.0), \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.sleep") as sleep:
        response: Response = client.post_graphql("query", {})
    assert response is success
    assert mock_request.call_count == 2
    assert sleep.call_args_list == [call(100), call(100)]


def test_post_graphql_waits_a_minute_after_secondary_limit_without_headers(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    limited: Response = __graphql_response(b'{"errors": [{"message": "You have exceeded a secondary rate limit"}]}')
    success: Response = __graphql_response(b'{"data": {"repository": {"name": "b"}}}')
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               side_effect=[limited, success]), \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.sleep") as sleep:
        assert client.post_graphql("query", {}) is success
    sleep.assert_called_once_with(60)


def test_post_graphql_returns_limited_ok_response_when_retries_run_out(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    limited: Response = __graphql_response(__graphql_limited_content)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               return_value=limited) as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.sleep") as sleep:
        assert client.post_graphql("query", {}) is limited
    assert mock_request.call_count == 4
    assert sleep.call_count == 3


def test_post_graphql_does_not_retry_not_found_error(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    not_found: Response = __graphql_response(b'{"data": {"repository": null}, "errors": [{"type": "NOT_FOUND"}]}')
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               return_value=not_found) as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.sleep") as sleep:
        assert client.post_graphql("query", {}) is not_found
    assert mock_request.call_count == 1
    sleep.assert_not_called()


def test_get_from_url_does_not_retry_ok_response_mentioning_rate_limit(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    readme: Response = __graphql_response(__graphql_limited_content)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               return_value=readme) as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rate_limit.time.sleep") as sleep:
        assert client.get_from_url("https://api.github.com/repos/a/b/readme") is readme
    assert mock_request.call_count == 1
    sleep.assert_not_called()


def test_is_graphql_limited_on_limited_ok_response(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    assert client.is_graphql_limited(__graphql_response(__graphql_limited_content))


def test_is_graphql_limited_on_not_found_error(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    assert not client.is_graphql_limited(__graphql_response(b'{"errors": [{"type": "NOT_FOUND"}]}'))


def test_post_graphql_raises_when_offline(tmp_path: Path):
    token_file: Path = __token_file(tmp_path)
    token_file.write_text("secret-token\n")
    client: GithubRestClient = GithubRestClient(offline=True, token_file=token_file)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request") as mock_request:
        with pytest.raises(RuntimeError, match="Offline mode is enabled"):
            client.post_graphql("query", {})
    mock_request.assert_not_called()


def test_get_from_url_sends_timeout(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               return_value=__response(200)) as mock_request:
        client.get_from_url("https://api.github.com/repos/a/b")
    assert mock_request.call_args.kwargs["timeout"] == 60


def test_post_graphql_sends_timeout(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               return_value=__response(200)) as mock_request:
        client.post_graphql("query", {})
    assert mock_request.call_args.kwargs["timeout"] == 60


@pytest.mark.parametrize("error", [Timeout("timed out"), RequestsConnectionError("connection reset")])
def test_retries_after_timeout_or_connection_error(tmp_path: Path, error: Exception):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               side_effect=[error, __response(200)]) as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rest_client.time.sleep") as sleep:
        response: Response = client.get_from_url("https://api.github.com/repos/a/b")
    assert response.status_code == 200
    assert mock_request.call_count == 2
    sleep.assert_called_once_with(5)


def test_raises_when_timeout_retries_run_out(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               side_effect=Timeout("timed out")) as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rest_client.time.sleep") as sleep:
        with pytest.raises(Timeout):
            client.post_graphql("query", {})
    assert mock_request.call_count == 4
    assert sleep.call_args_list == [call(5), call(10), call(15)]


def test_does_not_retry_other_request_errors(tmp_path: Path):
    client: GithubRestClient = __make_client(tmp_path)
    with patch("anki_addons_dataset.collector.github.github_rest_client.requests.request",
               side_effect=InvalidURL("bad url")) as mock_request, \
            patch("anki_addons_dataset.collector.github.github_rest_client.time.sleep") as sleep:
        with pytest.raises(InvalidURL):
            client.get_from_url("https://api.github.com/repos/a/b")
    assert mock_request.call_count == 1
    sleep.assert_not_called()
