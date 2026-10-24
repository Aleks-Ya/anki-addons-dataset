import dataclasses
from datetime import datetime
from typing import Any, Optional

from anki_addons_dataset.collector.github.handler.repo_handler import RepoHandler
from anki_addons_dataset.common.data_types import GithubRelease, GithubReleaseAsset


class ReleasesRepoHandler(RepoHandler):

    def _get_raw_filename(self) -> str:
        return "releases"

    def _get_stage_filename(self) -> str:
        return "releases"

    def get_url(self) -> str:
        return f"https://api.github.com/repos/{self._repo.user}/{self._repo.repo_name}/releases?per_page=100"

    def _extract_return_value_from_dict(self, content_obj: Any) -> Optional[list[GithubRelease]]:
        if not isinstance(content_obj, list):
            return None
        return [self.__parse_release(release) for release in content_obj if not release.get("draft")]

    def _prepare_stage_dict(self, return_value: Optional[list[GithubRelease]]) -> dict[str, Any]:
        releases: Optional[list[dict[str, Any]]] = [dataclasses.asdict(release) for release in return_value] \
            if return_value is not None else None
        return {"releases": releases}

    @staticmethod
    def __parse_release(release: dict[str, Any]) -> GithubRelease:
        published_at: Optional[str] = release.get("published_at")
        return GithubRelease(
            tag_name=release["tag_name"],
            name=release.get("name") or None,
            published_at=datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ") if published_at else None,
            prerelease=bool(release.get("prerelease")),
            assets=[GithubReleaseAsset(asset["name"], asset.get("size", 0), asset.get("download_count", 0))
                    for asset in release.get("assets", [])])
