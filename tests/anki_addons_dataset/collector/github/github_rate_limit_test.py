from itertools import chain, repeat
from typing import Iterator, Optional
from unittest.mock import Mock, patch

from requests import Response
from requests.structures import CaseInsensitiveDict

from anki_addons_dataset.collector.github.github_rate_limit import GithubGraphqlRateLimit, GithubRateLimit

NOW: int = 1688520000
RESET_TIMESTAMP: int = NOW + 20 * 60


def test_wait_for_reset():
    github_rate_limit: GithubRateLimit = GithubRateLimit()
    github_rate_limit.wait_for_reset()
    assert github_rate_limit.get_limit_remaining() is None


def test_update_rate_limit():
    github_rate_limit: GithubRateLimit = GithubRateLimit()
    github_rate_limit.wait_for_reset()
    assert github_rate_limit.get_limit_remaining() is None
    response: Response = Response()
    response.headers = CaseInsensitiveDict({
        "retry-after": "10",
        "x-ratelimit-remaining": "99",
        "x-ratelimit-reset": "1688520000"
    })
    github_rate_limit.update_rate_limit(response)
    assert github_rate_limit.get_limit_remaining() == 99


def test_exhausted_limit_waits_until_reset():
    github_rate_limit: GithubRateLimit = __rate_limit(remaining="0", reset=str(RESET_TIMESTAMP))
    __wait_for_reset(github_rate_limit).assert_called_once_with(20 * 60)


def test_reset_in_the_past_does_not_sleep_a_negative_time():
    github_rate_limit: GithubRateLimit = __rate_limit(remaining="0", reset=str(NOW - 1))
    __wait_for_reset(github_rate_limit).assert_called_once_with(0)


def test_exhausted_limit_without_reset_does_not_wait():
    github_rate_limit: GithubRateLimit = __rate_limit(remaining="0", reset=None)
    __wait_for_reset(github_rate_limit).assert_not_called()


def test_remaining_limit_does_not_wait():
    github_rate_limit: GithubRateLimit = __rate_limit(remaining="99", reset=str(RESET_TIMESTAMP))
    __wait_for_reset(github_rate_limit).assert_not_called()


def test_exhausted_quota_is_limited():
    assert GithubRateLimit().is_limited(__limited(403, {"x-ratelimit-remaining": "0"}))


def test_retry_after_is_limited():
    assert GithubRateLimit().is_limited(__limited(403, {"retry-after": "60"}))


def test_too_many_requests_is_limited():
    assert GithubRateLimit().is_limited(__limited(429, {"retry-after": "60"}))


def test_too_many_requests_without_markers_is_limited():
    assert GithubRateLimit().is_limited(__limited(429, {"x-ratelimit-remaining": "4000"}, b'{"message": "Too many"}'))


def test_too_many_requests_without_markers_waits_a_minute():
    response: Response = __limited(429, {"x-ratelimit-remaining": "4000"}, b'{"message": "Too many"}')
    __wait_after_limited(response).assert_called_once_with(60)


def test_rate_limit_message_is_limited():
    assert GithubRateLimit().is_limited(
        __limited(403, {"x-ratelimit-remaining": "99"}, b'{"message": "You have exceeded a secondary rate limit"}'))


def test_forbidden_without_rate_limit_is_not_limited():
    assert not GithubRateLimit().is_limited(
        __limited(403, {"x-ratelimit-remaining": "99"}, b'{"message": "Resource not accessible"}'))


def test_other_status_is_not_limited():
    assert not GithubRateLimit().is_limited(__limited(200, {"x-ratelimit-remaining": "0"}))


def test_limited_wait_prefers_retry_after():
    response: Response = __limited(403, {"retry-after": "30", "x-ratelimit-reset": str(RESET_TIMESTAMP)})
    __wait_after_limited(response).assert_called_once_with(30)


def test_limited_wait_until_reset():
    response: Response = __limited(403, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(RESET_TIMESTAMP)})
    __wait_after_limited(response).assert_called_once_with(20 * 60)


def test_limited_wait_with_past_reset_sleeps_a_minute():
    response: Response = __limited(403, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(NOW - 1)})
    __wait_after_limited(response).assert_called_once_with(60)


def test_limited_wait_with_reset_now_sleeps_a_minute():
    response: Response = __limited(403, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(NOW)})
    __wait_after_limited(response).assert_called_once_with(60)


def test_limited_wait_without_headers_sleeps_a_minute():
    response: Response = __limited(403, {}, b'{"message": "You have exceeded a secondary rate limit"}')
    __wait_after_limited(response).assert_called_once_with(60)


def test_limited_wait_with_quota_left_ignores_far_reset():
    response: Response = __limited(403, {"x-ratelimit-remaining": "4000", "x-ratelimit-reset": str(RESET_TIMESTAMP)},
                                   b'{"message": "You have exceeded a secondary rate limit"}')
    __wait_after_limited(response).assert_called_once_with(60)


def test_limited_wait_with_quota_left_ignores_near_reset():
    response: Response = __limited(403, {"x-ratelimit-remaining": "4000", "x-ratelimit-reset": str(NOW + 2)},
                                   b'{"message": "You have exceeded a secondary rate limit"}')
    __wait_after_limited(response).assert_called_once_with(60)


def test_limited_wait_without_remaining_ignores_reset():
    response: Response = __limited(403, {"x-ratelimit-reset": str(RESET_TIMESTAMP)},
                                   b'{"message": "You have exceeded a secondary rate limit"}')
    __wait_after_limited(response).assert_called_once_with(60)


def test_limited_wait_subtracts_lock_wait_from_retry_after():
    response: Response = __limited(403, {"retry-after": "30"})
    __wait_after_lock_wait(response, 20).assert_called_once_with(10)


def test_limited_wait_subtracts_lock_wait_from_default():
    response: Response = __limited(403, {}, b'{"message": "You have exceeded a secondary rate limit"}')
    __wait_after_lock_wait(response, 20).assert_called_once_with(40)


def test_limited_wait_longer_lock_wait_still_sleeps():
    response: Response = __limited(403, {"retry-after": "30"})
    __wait_after_lock_wait(response, 40).assert_called_once_with(1)


def test_limited_wait_until_reset_is_measured_after_lock_wait():
    response: Response = __limited(403, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(RESET_TIMESTAMP)})
    __wait_after_lock_wait(response, 20).assert_called_once_with(20 * 60 - 20)


def test_rest_ok_response_mentioning_rate_limit_is_not_limited():
    assert not GithubRateLimit().is_limited(__limited(200, {}, b'{"errors": [{"type": "RATE_LIMITED"}]}'))


def test_graphql_ok_with_rate_limited_type_is_limited():
    assert GithubGraphqlRateLimit().is_limited(__limited(200, {}, b'{"errors": [{"type": "RATE_LIMITED"}]}'))


def test_graphql_ok_with_secondary_limit_message_is_limited():
    assert GithubGraphqlRateLimit().is_limited(
        __limited(200, {}, b'{"errors": [{"message": "You have exceeded a secondary rate limit"}]}'))


def test_graphql_forbidden_with_retry_after_is_limited():
    assert GithubGraphqlRateLimit().is_limited(__limited(403, {"retry-after": "60"}))


def test_graphql_ok_with_not_found_error_is_not_limited():
    assert not GithubGraphqlRateLimit().is_limited(
        __limited(200, {}, b'{"data": {"repository": null}, "errors": [{"type": "NOT_FOUND", "message": "No repo"}]}'))


def test_graphql_ok_with_data_is_not_limited():
    assert not GithubGraphqlRateLimit().is_limited(__limited(200, {}, b'{"data": {"repository": {"name": "a"}}}'))


def test_graphql_ok_with_empty_body_is_not_limited():
    assert not GithubGraphqlRateLimit().is_limited(__limited(200, {}))


def test_graphql_ok_with_non_json_body_is_not_limited():
    assert not GithubGraphqlRateLimit().is_limited(__limited(200, {}, b"<html>rate limit</html>"))


def test_graphql_ok_with_non_dict_body_is_not_limited():
    assert not GithubGraphqlRateLimit().is_limited(__limited(200, {}, b'["rate limit"]'))


def test_graphql_server_error_is_not_limited():
    assert not GithubGraphqlRateLimit().is_limited(__limited(502, {}, b'{"errors": [{"type": "RATE_LIMITED"}]}'))


def __wait_after_limited(response: Response) -> Mock:
    sleep: Mock = Mock()
    with patch("time.time", Mock(return_value=float(NOW))), patch("time.sleep", sleep):
        GithubRateLimit().wait_after_limited(response)
    return sleep


def __wait_after_lock_wait(response: Response, lock_wait_seconds: int) -> Mock:
    sleep: Mock = Mock()
    times: Iterator[float] = chain([float(NOW)], repeat(float(NOW + lock_wait_seconds)))
    with patch("time.time", Mock(side_effect=times)), patch("time.sleep", sleep):
        GithubRateLimit().wait_after_limited(response)
    return sleep


def __limited(status_code: int, headers: dict[str, str], content: bytes = b"") -> Response:
    response: Response = Response()
    response.status_code = status_code
    response.headers = CaseInsensitiveDict(headers)
    response._content = content
    return response


def __wait_for_reset(github_rate_limit: GithubRateLimit) -> Mock:
    sleep: Mock = Mock()
    with patch("time.time", Mock(return_value=float(NOW))), patch("time.sleep", sleep):
        github_rate_limit.wait_for_reset()
    return sleep


def __rate_limit(remaining: str, reset: Optional[str]) -> GithubRateLimit:
    github_rate_limit: GithubRateLimit = GithubRateLimit()
    headers: dict[str, str] = {"x-ratelimit-remaining": remaining}
    if reset is not None:
        headers["x-ratelimit-reset"] = reset
    response: Response = Response()
    response.headers = CaseInsensitiveDict(headers)
    github_rate_limit.update_rate_limit(response)
    return github_rate_limit
