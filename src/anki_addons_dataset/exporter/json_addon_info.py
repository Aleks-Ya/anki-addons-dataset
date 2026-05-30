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
    last_commit: Optional[str]
    links: list[Link]
    action_count: Optional[int]
    tests_count: Optional[int]


@dataclass
class Forum:
    anki_forum_url: Optional[str]
    topic_slug: Optional[str]
    topic_id: Optional[int]
    last_posted_at: Optional[str]
    posts_count: Optional[int]


@dataclass
class Branch:
    min_version: Optional[str]
    max_version: Optional[str]
    updated: Optional[str]


@dataclass
class AnkiWeb:
    title: str
    addon_page_url: str
    addon_page_content: str
    rating: int
    update_date: str
    anki_version: str
    branches: list[Branch]
    links: list[str]
    likes: int
    dislikes: int


@dataclass
class Details:
    id: int
    anki_web: AnkiWeb
    github: Optional[GitHub]
    forum: Optional[Forum]


class JsonAddonInfo:
    @staticmethod
    def addon_infos_to_json(addon_infos: AddonInfos) -> list[Details]:
        json_list: list[Details] = []
        for addon in addon_infos:
            github: Optional[GitHub] = JsonAddonInfo.__github(addon)
            forum: Optional[Forum] = JsonAddonInfo.__forum(addon)
            branches: list[Branch] = JsonAddonInfo.__branches(addon)
            anki_web: AnkiWeb = AnkiWeb(addon.header.title, addon.header.addon_page_url, addon.page.content,
                                        addon.header.rating, addon.header.update_date, addon.header.anki_version,
                                        branches, addon.page.other_links, addon.page.like_number,
                                        addon.page.dislike_number)
            json_obj: Details = Details(addon.header.id, anki_web, github, forum)
            json_list.append(json_obj)
        return json_list

    @staticmethod
    def __github(addon: AddonInfo) -> Optional[GitHub]:
        if not addon.github or not addon.github.github_repo:
            return None
        user: str = addon.github.github_repo.user
        repo_str: str = addon.github.github_repo.repo_name
        links: list[Link] = [Link(link.url, link.user.user_name, link.repo.repo_name if link.repo else None)
                             for link in addon.github.github_links]
        last_commit_str: Optional[str] = addon.github.last_commit.isoformat() if addon.github.last_commit else None
        return GitHub(user, repo_str, addon.github.languages, addon.github.stars,
                      last_commit_str, links, addon.github.action_count,
                      addon.github.tests_count)

    @staticmethod
    def __forum(addon: AddonInfo) -> Optional[Forum]:
        if not addon or not addon.forum:
            return None
        anki_forum_url: Optional[str] = addon.forum.anki_forum_url
        slug: Optional[str] = addon.forum.topic_slug
        topic_id: Optional[int] = addon.forum.topic_id
        last_posted_at: str = str(addon.forum.last_posted_at)
        posts_count: Optional[int] = addon.forum.posts_count
        return Forum(anki_forum_url, slug, topic_id, last_posted_at, posts_count)

    @staticmethod
    def __branches(addon: AddonInfo) -> list[Branch]:
        return [Branch(branch.min_anki_version, branch.max_anki_version, str(branch.updated))
                for branch in addon.page.branches]
