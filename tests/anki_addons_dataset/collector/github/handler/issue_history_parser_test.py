from datetime import datetime
from typing import Any, Optional

from anki_addons_dataset.collector.github.handler.issue_history_parser import IssueHistoryParser
from anki_addons_dataset.common.data_types import GithubIssueHistory

__author: dict[str, str] = {"login": "reporter", "__typename": "User"}
__maintainer: dict[str, str] = {"login": "maintainer", "__typename": "User"}
__bot: dict[str, str] = {"login": "dependabot", "__typename": "Bot"}


def __response(author: Optional[dict[str, str]], created_at: str) -> dict[str, Any]:
    return {"createdAt": created_at, "authorAssociation": "OWNER", "author": author}


def __issue(author: Optional[dict[str, str]], comments: list[dict[str, Any]]) -> dict[str, Any]:
    return {"createdAt": "2026-01-01T00:00:00Z", "closedAt": None, "state": "OPEN", "authorAssociation": "NONE",
            "author": author, "comments": {"nodes": comments}}


def __pull_request(state: str, association: str, author: Optional[dict[str, str]] = None,
                   comments: Optional[list[dict[str, Any]]] = None,
                   reviews: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    return {"createdAt": "2026-01-01T00:00:00Z", "closedAt": None,
            "mergedAt": "2026-01-02T00:00:00Z" if state == "MERGED" else None, "state": state,
            "authorAssociation": association, "author": author or __author,
            "comments": {"nodes": comments or []}, "reviews": {"nodes": reviews or []}}


def __content(issues: Optional[list[dict[str, Any]]] = None, pull_requests: Optional[list[dict[str, Any]]] = None,
              closed_at: Optional[list[str]] = None) -> dict[str, Any]:
    return {"data": {"repository": {
        "hasIssuesEnabled": True,
        "openIssues": {"totalCount": 1},
        "closedIssues": {"totalCount": 2},
        "openPullRequests": {"totalCount": 3},
        "closedPullRequests": {"totalCount": 4},
        "mergedPullRequests": {"totalCount": 5},
        "recentlyClosedIssues": {"nodes": [{"closedAt": value} for value in closed_at or []]},
        "recentIssues": {"nodes": issues or []},
        "recentPullRequests": {"nodes": pull_requests or []},
    }}}


def __parse(content: dict[str, Any]) -> GithubIssueHistory:
    history: Optional[GithubIssueHistory] = IssueHistoryParser.parse(content)
    assert history is not None
    return history


def test_empty_repo_has_counts_and_no_figures():
    assert __parse(__content()) == GithubIssueHistory(True, 1, 2, 3, 4, 5, None, None, 0, 0, 0)


def test_missing_repository():
    assert IssueHistoryParser.parse({"data": {"repository": None}, "errors": [{"type": "NOT_FOUND"}]}) is None


def test_last_closed_is_the_maximum_of_an_unordered_page():
    closed_at: list[str] = ["2022-08-11T23:38:24Z", "2026-10-29T14:24:15Z", "2026-10-28T14:57:20Z"]
    assert __parse(__content(closed_at=closed_at)).last_issue_closed_at == datetime(2026, 10, 29, 14, 24, 15)


def test_first_response_skips_the_author_and_bots():
    comments: list[dict[str, Any]] = [__response(__author, "2026-01-01T01:00:00Z"),
                                      __response(__bot, "2026-01-01T02:00:00Z"),
                                      __response(__maintainer, "2026-01-01T03:00:00Z")]
    history: GithubIssueHistory = __parse(__content(issues=[__issue(__author, comments)]))
    assert history.median_first_response_hours == 3
    assert history.first_response_sample == 1


def test_first_response_takes_the_earliest_of_comments_and_reviews():
    pull_request: dict[str, Any] = __pull_request("OPEN", "NONE",
                                                  comments=[__response(__maintainer, "2026-01-01T05:00:00Z")],
                                                  reviews=[__response(__maintainer, "2026-01-01T02:00:00Z")])
    assert __parse(__content(pull_requests=[pull_request])).median_first_response_hours == 2


def test_median_leaves_out_unanswered_and_bot_opened_items():
    issues: list[dict[str, Any]] = [
        __issue(__author, [__response(__maintainer, "2026-01-01T01:00:00Z")]),
        __issue(__author, [__response(__maintainer, "2026-01-01T02:00:00Z")]),
        __issue(__author, [__response(__maintainer, "2026-01-02T00:00:00Z")]),
        __issue(__author, []),
        __issue(__bot, [__response(__maintainer, "2026-01-11T00:00:00Z")]),
    ]
    history: GithubIssueHistory = __parse(__content(issues=issues))
    assert history.median_first_response_hours == 2
    assert history.first_response_sample == 3


def test_outside_prs_leave_out_maintainers_bots_and_open_ones():
    pull_requests: list[dict[str, Any]] = [
        __pull_request("MERGED", "NONE"),
        __pull_request("MERGED", "CONTRIBUTOR"),
        __pull_request("CLOSED", "FIRST_TIME_CONTRIBUTOR"),
        __pull_request("OPEN", "NONE"),
        __pull_request("MERGED", "OWNER"),
        __pull_request("MERGED", "MEMBER"),
        __pull_request("CLOSED", "COLLABORATOR"),
        __pull_request("MERGED", "NONE", author=__bot),
    ]
    history: GithubIssueHistory = __parse(__content(pull_requests=pull_requests))
    assert history.outside_prs_merged == 2
    assert history.outside_prs_decided == 3


def test_deleted_accounts():
    answered_by_deleted: dict[str, Any] = __issue(__author, [__response(None, "2026-01-01T04:00:00Z")])
    deleted_author_and_commenter: dict[str, Any] = __issue(None, [__response(None, "2026-01-01T09:00:00Z")])
    history: GithubIssueHistory = __parse(__content(issues=[answered_by_deleted, deleted_author_and_commenter]))
    assert history.median_first_response_hours == 4
    assert history.first_response_sample == 1
