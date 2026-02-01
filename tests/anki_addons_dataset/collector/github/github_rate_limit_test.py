from requests import Response
from requests.structures import CaseInsensitiveDict

from anki_addons_dataset.collector.github.github_rate_limit import GithubRateLimit


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
