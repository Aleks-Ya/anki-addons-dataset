import dataclasses
from typing import Any, Optional

from requests import Response

from anki_addons_dataset.collector.github.github_rest_client import GithubRestClient
from anki_addons_dataset.collector.github.handler.issue_history_parser import IssueHistoryParser
from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler
from anki_addons_dataset.common.data_types import GithubIssueHistory


class IssueHistoryRepoHandler(RepoHandler):
    # GitHub cannot order issues by closedAt: the last close is the maximum over the most recently updated ones.
    query: str = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    hasIssuesEnabled
    openIssues: issues(states: OPEN) { totalCount }
    closedIssues: issues(states: CLOSED) { totalCount }
    openPullRequests: pullRequests(states: OPEN) { totalCount }
    closedPullRequests: pullRequests(states: CLOSED) { totalCount }
    mergedPullRequests: pullRequests(states: MERGED) { totalCount }
    recentlyClosedIssues: issues(states: CLOSED, first: 20, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes { closedAt }
    }
    recentIssues: issues(first: 100, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        createdAt closedAt state authorAssociation author { login __typename }
        comments(first: 10) { nodes { createdAt authorAssociation author { login __typename } } }
      }
    }
    recentPullRequests: pullRequests(first: 100, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        createdAt closedAt mergedAt state authorAssociation author { login __typename }
        comments(first: 10) { nodes { createdAt authorAssociation author { login __typename } } }
        reviews(first: 10) { nodes { createdAt authorAssociation author { login __typename } } }
      }
    }
  }
}
"""

    def get_variables(self) -> dict[str, str]:
        return {"owner": self._repo.user, "name": self._repo.repo_name}

    def get_url(self) -> str:
        return GithubRestClient.graphql_url

    def is_complete(self, response: Response) -> bool:
        if response.status_code != 200:
            return False
        try:
            body: Any = response.json()
        except ValueError:
            return False
        if not isinstance(body, dict):
            return False
        return all(error.get("type") == "NOT_FOUND" for error in body.get("errors", []))

    def _get_raw_filename(self) -> str:
        return "issue-history"

    def _get_stage_filename(self) -> str:
        return "issue-history"

    def _extract_return_value_from_dict(self, content_obj: dict[str, Any]) -> Optional[GithubIssueHistory]:
        return IssueHistoryParser.parse(content_obj)

    def _prepare_stage_dict(self, return_value: Optional[GithubIssueHistory]) -> dict[str, Any]:
        return dataclasses.asdict(return_value) if return_value else {}
