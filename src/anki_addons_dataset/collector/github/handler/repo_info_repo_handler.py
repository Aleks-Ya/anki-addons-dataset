from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler
from anki_addons_dataset.common.data_types import SpdxLicense, Topic, URL


@dataclass
class GithubRepoMeta:
    """Developer-facing fields extracted from the `GET /repos/{u}/{r}` response (already fetched for stars)."""
    license: Optional[SpdxLicense] = None
    forks: Optional[int] = None
    open_issues: Optional[int] = None
    size_kb: Optional[int] = None
    topics: list[Topic] = field(default_factory=list)
    repo_description: Optional[str] = None
    homepage: Optional[URL] = None
    archived: Optional[bool] = None
    pushed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class RepoInfoRepoHandler(RepoHandler):
    """Reads the same `info.json` raw file as StarsRepoHandler, so it reuses the cache without an extra API call."""

    def _get_raw_filename(self) -> str:
        return "info"

    def _get_stage_filename(self) -> str:
        return "repo-info"

    def get_url(self) -> str:
        return f"https://api.github.com/repos/{self._repo.user}/{self._repo.repo_name}"

    def _extract_return_value_from_dict(self, content_obj: dict[str, Any]) -> GithubRepoMeta:
        license_obj: Optional[dict[str, Any]] = content_obj.get("license")
        spdx: Optional[str] = license_obj.get("spdx_id") if license_obj else None
        return GithubRepoMeta(
            license=SpdxLicense(spdx) if spdx and spdx != "NOASSERTION" else None,
            forks=content_obj.get("forks_count"),
            open_issues=content_obj.get("open_issues_count"),
            size_kb=content_obj.get("size"),
            topics=[Topic(topic) for topic in content_obj.get("topics", [])],
            repo_description=content_obj.get("description"),
            homepage=URL(content_obj["homepage"]) if content_obj.get("homepage") else None,
            archived=content_obj.get("archived"),
            pushed_at=self.__parse_date(content_obj.get("pushed_at")),
            created_at=self.__parse_date(content_obj.get("created_at")),
        )

    def _prepare_stage_dict(self, return_value: GithubRepoMeta) -> dict[str, Any]:
        return {
            "license": return_value.license,
            "forks": return_value.forks,
            "open_issues": return_value.open_issues,
            "size_kb": return_value.size_kb,
            "topics": return_value.topics,
            "repo_description": return_value.repo_description,
            "homepage": return_value.homepage,
            "archived": return_value.archived,
            "pushed_at": return_value.pushed_at,
            "created_at": return_value.created_at,
        }

    def get_not_found_return_value(self) -> GithubRepoMeta:
        return GithubRepoMeta()

    @staticmethod
    def __parse_date(value: Optional[str]) -> Optional[datetime]:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ") if value else None
