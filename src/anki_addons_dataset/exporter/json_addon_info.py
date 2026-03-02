from dataclasses import dataclass
from typing import Optional

from anki_addons_dataset.common.data_types import AddonInfos, AddonInfo


@dataclass
class Link:
    url: str
    user: Optional[str]
    repo: Optional[str]


@dataclass
class GitHub:
    user: Optional[str]
    repo: Optional[str]
    languages: list[str]
    stars: int
    last_commit: str
    links: list[Link]
    action_count: int
    tests_count: int


@dataclass
class Forum:
    anki_forum_url: Optional[str]
    topic_slug: Optional[str]
    topic_id: Optional[int]
    last_posted_at: Optional[str]
    posts_count: Optional[int]


@dataclass
class Version:
    min_version: Optional[str]
    max_version: Optional[str]
    updated: Optional[str]


@dataclass
class Details:
    id: int
    name: str
    addon_page: str
    rating: int
    update_date: str
    versions_str: str
    versions: list[Version]
    github: Optional[GitHub]
    forum: Optional[Forum]
    links: list[str]
    likes: int
    dislikes: int


class JsonAddonInfo:
    @staticmethod
    def addon_infos_to_json(addon_infos: AddonInfos) -> list[Details]:
        json_list: list[Details] = []
        for addon in addon_infos:
            github: Optional[GitHub] = JsonAddonInfo.__github(addon)
            forum: Optional[Forum] = JsonAddonInfo.__forum(addon)
            versions: list[Version] = JsonAddonInfo.__versions(addon)
            json_obj: Details = Details(addon.header.id, addon.header.name, addon.header.addon_page,
                                        addon.header.rating, addon.header.update_date, addon.header.versions, versions,
                                        github, forum, addon.page.other_links, addon.page.like_number,
                                        addon.page.dislike_number)
            json_list.append(json_obj)
        return json_list

    @staticmethod
    def __github(addon: AddonInfo) -> Optional[GitHub]:
        if not addon.github.github_repo:
            return None
        user: str = addon.github.github_repo.user
        repo_str: str = addon.github.github_repo.repo_name
        links: list[Link] = [Link(link.url, link.user.user_name, link.repo.repo_name if link.repo else None)
                             for link in addon.github.github_links]
        last_commit_str: str = addon.github.last_commit.isoformat() if addon.github.last_commit else None
        return GitHub(user, repo_str, addon.github.languages, addon.github.stars,
                      last_commit_str, links, addon.github.action_count,
                      addon.github.tests_count)

    @staticmethod
    def __forum(addon: AddonInfo) -> Optional[Forum]:
        if not addon.forum:
            return None
        anki_forum_url: str = addon.forum.anki_forum_url
        slug: str = addon.forum.topic_slug
        topic_id: int = addon.forum.topic_id
        last_posted_at: str = str(addon.forum.last_posted_at)
        posts_count: int = addon.forum.posts_count
        return Forum(anki_forum_url, slug, topic_id, last_posted_at, posts_count)

    @staticmethod
    def __versions(addon: AddonInfo) -> list[Version]:
        return [Version(version.min_version, version.max_version, str(version.updated))
                for version in addon.page.versions]
