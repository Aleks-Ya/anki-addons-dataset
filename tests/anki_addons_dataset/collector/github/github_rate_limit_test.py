from typing import Optional
from unittest.mock import Mock, patch

from requests import Response
from requests.structures import CaseInsensitiveDict

from anki_addons_dataset.collector.github.github_rate_limit import GithubRateLimit

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
