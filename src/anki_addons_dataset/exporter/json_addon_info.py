from dataclasses import dataclass
from typing import Optional

from anki_addons_dataset.common.data_types import AddonInfos


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
    anki_forum_url: Optional[str]
    github: Optional[GitHub]
    links: list[str]
    likes: int
    dislikes: int


class JsonAddonInfo:
    @staticmethod
    def addon_infos_to_json(addon_infos: AddonInfos) -> list[Details]:
        json_list: list[Details] = []
        for addon in addon_infos:
            links: list[Link] = [Link(link.url,
                                      link.user.user_name,
                                      link.repo.repo_name if link.repo else None)
                                 for link in addon.github.github_links]
            last_commit_str: str = addon.github.last_commit.isoformat() if addon.github.last_commit else None
            if addon.github.github_repo:
                user: str = addon.github.github_repo.user
                repo_str: str = addon.github.github_repo.repo_name
                github: Optional[GitHub] = GitHub(user, repo_str, addon.github.languages, addon.github.stars,
                                                  last_commit_str, links, addon.github.action_count,
                                                  addon.github.tests_count)
            else:
                github: Optional[GitHub] = None
            versions: list[Version] = [Version(version.min_version, version.max_version, str(version.updated))
                                       for version in addon.page.versions]
            json_obj: Details = Details(addon.header.id, addon.header.name, addon.header.addon_page,
                                        addon.header.rating, addon.header.update_date, addon.header.versions, versions,
                                        addon.page.anki_forum_url, github, addon.page.other_links,
                                        addon.page.like_number, addon.page.dislike_number)
            json_list.append(json_obj)
        return json_list
