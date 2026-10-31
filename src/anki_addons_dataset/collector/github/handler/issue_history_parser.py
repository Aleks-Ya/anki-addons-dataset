import statistics
from datetime import datetime
from typing import Any, Optional

from anki_addons_dataset.common.data_types import GithubIssueHistory


class IssueHistoryParser:
    __maintainer_associations: frozenset[str] = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})

    @staticmethod
    def parse(content: dict[str, Any]) -> Optional[GithubIssueHistory]:
        repository: Optional[dict[str, Any]] = (content.get("data") or {}).get("repository")
        if not repository:
            return None
        issues: list[dict[str, Any]] = repository["recentIssues"]["nodes"]
        pull_requests: list[dict[str, Any]] = repository["recentPullRequests"]["nodes"]
        response_hours: list[float] = IssueHistoryParser.__response_hours(issues + pull_requests)
        outside_prs: list[dict[str, Any]] = [pull_request for pull_request in pull_requests
                                             if IssueHistoryParser.__is_decided_outside_pr(pull_request)]
        return GithubIssueHistory(
            has_issues_enabled=repository["hasIssuesEnabled"],
            open_issue_count=repository["openIssues"]["totalCount"],
            closed_issue_count=repository["closedIssues"]["totalCount"],
            open_pr_count=repository["openPullRequests"]["totalCount"],
            closed_pr_count=repository["closedPullRequests"]["totalCount"],
            merged_pr_count=repository["mergedPullRequests"]["totalCount"],
            last_issue_closed_at=IssueHistoryParser.__last_closed_at(repository["recentlyClosedIssues"]["nodes"]),
            median_first_response_hours=round(statistics.median(response_hours), 2) if response_hours else None,
            first_response_sample=len(response_hours),
            outside_prs_merged=sum(1 for pull_request in outside_prs if pull_request["mergedAt"]),
            outside_prs_decided=len(outside_prs),
        )

    @staticmethod
    def __last_closed_at(issues: list[dict[str, Any]]) -> Optional[datetime]:
        closed_at: list[datetime] = [IssueHistoryParser.__parse_date(issue["closedAt"])
                                     for issue in issues if issue["closedAt"]]
        return max(closed_at, default=None)

    @staticmethod
    def __response_hours(items: list[dict[str, Any]]) -> list[float]:
        hours: list[Optional[float]] = [IssueHistoryParser.__first_response_hours(item) for item in items
                                        if not IssueHistoryParser.__is_bot(item["author"])]
        return [value for value in hours if value is not None]

    @staticmethod
    def __first_response_hours(item: dict[str, Any]) -> Optional[float]:
        reviews: list[dict[str, Any]] = item["reviews"]["nodes"] if "reviews" in item else []
        responses: list[datetime] = [IssueHistoryParser.__parse_date(response["createdAt"])
                                     for response in item["comments"]["nodes"] + reviews
                                     if IssueHistoryParser.__is_response(response, item)]
        if not responses:
            return None
        return (min(responses) - IssueHistoryParser.__parse_date(item["createdAt"])).total_seconds() / 3600

    @staticmethod
    def __is_response(response: dict[str, Any], item: dict[str, Any]) -> bool:
        author: Optional[dict[str, Any]] = response["author"]
        return not IssueHistoryParser.__is_bot(author) \
            and IssueHistoryParser.__login(author) != IssueHistoryParser.__login(item["author"])

    @staticmethod
    def __is_decided_outside_pr(pull_request: dict[str, Any]) -> bool:
        return pull_request["state"] != "OPEN" \
            and not IssueHistoryParser.__is_bot(pull_request["author"]) \
            and pull_request["authorAssociation"] not in IssueHistoryParser.__maintainer_associations

    @staticmethod
    def __is_bot(actor: Optional[dict[str, Any]]) -> bool:
        return actor is not None and actor["__typename"] == "Bot"

    @staticmethod
    def __login(actor: Optional[dict[str, Any]]) -> Optional[str]:
        return actor["login"] if actor else None

    @staticmethod
    def __parse_date(value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
