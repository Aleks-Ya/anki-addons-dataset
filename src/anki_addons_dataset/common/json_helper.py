import dataclasses
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from anki_addons_dataset.common.data_types import AddonInfo, AddonInfos, AddonHeader, AddonPage, AddonBranch, \
    GithubInfo, GitHubLink, GitHubUser, GithubRepo, AnkiForumInfo, AddonId, AnkiVersion, HtmlStr, URL, \
    GithubUserName, GithubRepoName, LanguageName, TopicSlug, TopicId, LastPostedAt, PostsCount, ScriptVersion


class JsonHelper:
    __script_version_key: str = "script_version"
    __addon_infos_key: str = "addon_infos"

    @staticmethod
    def write_addon_info_to_file(addon_infos: AddonInfo, file: Path) -> None:
        file.parent.mkdir(parents=True, exist_ok=True)
        content_json: str = json.dumps(dataclasses.asdict(addon_infos), indent=2, default=JsonHelper.__date_serializer)
        file.write_text(content_json)

    @staticmethod
    def write_addon_infos_dump(addon_infos: AddonInfos, script_version: ScriptVersion, file: Path) -> None:
        file.parent.mkdir(parents=True, exist_ok=True)
        envelope: dict[str, Any] = {
            JsonHelper.__script_version_key: script_version,
            JsonHelper.__addon_infos_key: [dataclasses.asdict(addon_info) for addon_info in addon_infos],
        }
        content_json: str = json.dumps(envelope, indent=2, default=JsonHelper.__date_serializer)
        file.write_text(content_json)

    @staticmethod
    def read_addon_infos_dump(file: Path) -> tuple[ScriptVersion, AddonInfos]:
        envelope: dict[str, Any] = json.loads(file.read_text())
        script_version: ScriptVersion = ScriptVersion(envelope[JsonHelper.__script_version_key])
        addon_infos: AddonInfos = AddonInfos(
            [JsonHelper.__addon_info_from_dict(item) for item in envelope[JsonHelper.__addon_infos_key]])
        return script_version, addon_infos

    @staticmethod
    def __addon_info_from_dict(data: dict[str, Any]) -> AddonInfo:
        return AddonInfo(
            header=JsonHelper.__addon_header_from_dict(data["header"]),
            page=JsonHelper.__addon_page_from_dict(data["page"]),
            github=JsonHelper.__github_info_from_dict(data["github"]),
            forum=JsonHelper.__anki_forum_info_from_dict(data["forum"]),
        )

    @staticmethod
    def __addon_header_from_dict(data: dict[str, Any]) -> AddonHeader:
        return AddonHeader(
            id=AddonId(data["id"]),
            title=data["title"],
            addon_page_url=data["addon_page_url"],
            rating=data["rating"],
            update_date=data["update_date"],
            anki_version=AnkiVersion(data["anki_version"]),
        )

    @staticmethod
    def __addon_page_from_dict(data: dict[str, Any]) -> AddonPage:
        return AddonPage(
            content=HtmlStr(data["content"]),
            like_number=data["like_number"],
            dislike_number=data["dislike_number"],
            branches=[JsonHelper.__addon_branch_from_dict(branch) for branch in data["branches"]],
            other_links=[URL(link) for link in data["other_links"]],
            description=data.get("description", ""),
        )

    @staticmethod
    def __addon_branch_from_dict(data: dict[str, Any]) -> AddonBranch:
        max_anki_version: Optional[str] = data["max_anki_version"]
        return AddonBranch(
            min_anki_version=AnkiVersion(data["min_anki_version"]),
            max_anki_version=AnkiVersion(max_anki_version) if max_anki_version is not None else None,
            updated=date.fromisoformat(data["updated"]),
        )

    @staticmethod
    def __github_info_from_dict(data: Optional[dict[str, Any]]) -> Optional[GithubInfo]:
        if data is None:
            return None
        last_commit: Optional[str] = data["last_commit"]
        return GithubInfo(
            github_links=[JsonHelper.__github_link_from_dict(link) for link in data["github_links"]],
            github_repo=JsonHelper.__github_repo_from_dict(data["github_repo"]),
            languages=[LanguageName(language) for language in data["languages"]],
            stars=data["stars"],
            last_commit=datetime.fromisoformat(last_commit) if last_commit is not None else None,
            action_count=data["action_count"],
            tests_count=data["tests_count"],
        )

    @staticmethod
    def __github_link_from_dict(data: dict[str, Any]) -> GitHubLink:
        return GitHubLink(
            url=URL(data["url"]),
            user=GitHubUser(user_name=GithubUserName(data["user"]["user_name"])),
            repo=JsonHelper.__github_repo_from_dict(data["repo"]),
        )

    @staticmethod
    def __github_repo_from_dict(data: Optional[dict[str, Any]]) -> Optional[GithubRepo]:
        if data is None:
            return None
        return GithubRepo(user=GithubUserName(data["user"]), repo_name=GithubRepoName(data["repo_name"]))

    @staticmethod
    def __anki_forum_info_from_dict(data: Optional[dict[str, Any]]) -> Optional[AnkiForumInfo]:
        if data is None:
            return None
        anki_forum_url: Optional[str] = data["anki_forum_url"]
        topic_slug: Optional[str] = data["topic_slug"]
        last_posted_at: Optional[str] = data["last_posted_at"]
        posts_count: Optional[int] = data["posts_count"]
        return AnkiForumInfo(
            anki_forum_url=URL(anki_forum_url) if anki_forum_url is not None else None,
            topic_slug=TopicSlug(topic_slug) if topic_slug is not None else None,
            topic_id=TopicId(data["topic_id"]) if data["topic_id"] is not None else None,
            last_posted_at=LastPostedAt(datetime.fromisoformat(last_posted_at)) if last_posted_at is not None else None,
            posts_count=PostsCount(posts_count) if posts_count is not None else None,
        )

    @staticmethod
    def write_dict_to_file(content: dict[str, Any], file: Path) -> None:
        file.parent.mkdir(parents=True, exist_ok=True)
        content_json: str = json.dumps(content, indent=2, default=JsonHelper.__date_serializer)
        file.write_text(content_json)

    @staticmethod
    def write_content_to_file(content: str, file: Path) -> None:
        JsonHelper.write_dict_to_file(json.loads(content), file)

    @staticmethod
    def __date_serializer(obj: object):
        if isinstance(obj, date):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
