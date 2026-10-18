from dataclasses import dataclass
from typing import Optional

from anki_addons_dataset.common.anki_version import AnkiVersionCodec
from anki_addons_dataset.common.data_types import AddonInfos, AddonInfo, AddonDescription, GithubInfo, AddonManifest, \
    AnkiPointVersion


@dataclass
class Link:
    url: str
    user: Optional[str]
    repo: Optional[str]


@dataclass
class AnkiWebLink:
    url: str
    section: str
    count: int
    texts: list[str]


@dataclass
class LanguageBytes:
    name: str
    bytes: int


@dataclass
class Manifest:
    package: Optional[str]
    name: Optional[str]
    conflicts: list[str]
    min_point_version: Optional[int]
    max_point_version: Optional[int]
    homepage: Optional[str]
    mod: Optional[int]
    min_version: Optional[str]
    max_version: Optional[str]
    max_version_kind: str


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
    license: Optional[str]
    forks: Optional[int]
    open_issues: Optional[int]
    size_kb: Optional[int]
    topics: list[str]
    repo_description: Optional[str]
    homepage: Optional[str]
    archived: Optional[bool]
    pushed_at: Optional[str]
    created_at: Optional[str]
    primary_language: Optional[str]
    language_bytes: list[LanguageBytes]
    manifest: Optional[Manifest]
    dependencies: list[str]
    readme: Optional[str]
    ai_tooling_markers: list[str]
    repo_source: Optional[str]


@dataclass
class Forum:
    anki_forum_url: Optional[str]
    topic_slug: Optional[str]
    topic_id: Optional[int]
    last_posted_at: Optional[str]
    posts_count: Optional[int]


@dataclass
class Ai:
    summary: Optional[str]
    model: Optional[str]
    tags: Optional[list[str]]


@dataclass
class Branch:
    min_version: Optional[str]
    max_version: Optional[str]
    updated: Optional[str]
    min_point_version: Optional[int]
    max_point_version: Optional[int]
    max_version_kind: str


@dataclass
class AnkiWeb:
    title: str
    addon_page_url: str
    addon_page_content: str
    contact_author_url: Optional[str]
    description: AddonDescription
    rating: int
    update_date: str
    anki_version: str
    anki_point_version: Optional[int]
    anki_version_kind: str
    branches: list[Branch]
    links: list[AnkiWebLink]
    likes: int
    dislikes: int
    ai_declaration_markers: list[str]
    description_language: Optional[str]
    description_language_confidence: Optional[float]


@dataclass
class Details:
    id: int
    anki_web: AnkiWeb
    github: Optional[GitHub]
    forum: Optional[Forum]
    ai: Optional[Ai]


class JsonAddonInfo:
    @staticmethod
    def addon_infos_to_json(addon_infos: AddonInfos) -> list[Details]:
        json_list: list[Details] = []
        for addon in addon_infos:
            github: Optional[GitHub] = JsonAddonInfo.__github(addon)
            forum: Optional[Forum] = JsonAddonInfo.__forum(addon)
            branches: list[Branch] = JsonAddonInfo.__branches(addon)
            anki_web: AnkiWeb = AnkiWeb(addon.header.title, addon.header.addon_page_url, addon.page.content,
                                        addon.page.contact_author_url, addon.page.description, addon.header.rating,
                                        addon.header.update_date, addon.header.anki_version,
                                        addon.header.anki_point_version, str(addon.header.anki_version_kind), branches,
                                        JsonAddonInfo.__anki_web_links(addon), addon.page.like_number, addon.page.dislike_number,
                                        list(addon.page.ai_declaration_markers), addon.page.description_language,
                                        addon.page.description_language_confidence)
            json_obj: Details = Details(addon.header.id, anki_web, github, forum, JsonAddonInfo.__ai(addon))
            json_list.append(json_obj)
        return json_list

    @staticmethod
    def __anki_web_links(addon: AddonInfo) -> list[AnkiWebLink]:
        return [AnkiWebLink(link.url, str(link.section), link.count, list(link.texts)) for link in addon.page.links]

    @staticmethod
    def __github(addon: AddonInfo) -> Optional[GitHub]:
        if not addon.github or not addon.github.github_repo:
            return None
        github: GithubInfo = addon.github
        user: str = github.github_repo.user
        repo_str: str = github.github_repo.repo_name
        links: list[Link] = [Link(link.url, link.user.user_name, link.repo.repo_name if link.repo else None)
                             for link in github.github_links]
        last_commit_str: Optional[str] = github.last_commit.isoformat() if github.last_commit else None
        pushed_at_str: Optional[str] = github.pushed_at.isoformat() if github.pushed_at else None
        created_at_str: Optional[str] = github.created_at.isoformat() if github.created_at else None
        manifest: Optional[Manifest] = JsonAddonInfo.__manifest(github.manifest)
        language_bytes: list[LanguageBytes] = [LanguageBytes(name, count)
                                               for name, count in github.language_bytes.items()]
        return GitHub(user, repo_str, github.languages, github.stars, last_commit_str, links, github.action_count,
                      github.tests_count, github.license, github.forks, github.open_issues, github.size_kb,
                      list(github.topics), github.repo_description, github.homepage, github.archived, pushed_at_str,
                      created_at_str, github.primary_language, language_bytes, manifest,
                      list(github.dependencies), github.readme, list(github.ai_tooling_markers),
                      str(github.repo_source) if github.repo_source else None)

    @staticmethod
    def __manifest(manifest: Optional[AddonManifest]) -> Optional[Manifest]:
        if manifest is None:
            return None
        min_version: Optional[str] = AnkiVersionCodec.to_str(AnkiPointVersion(manifest.min_point_version)) \
            if manifest.min_point_version is not None and manifest.min_point_version > 0 else None
        max_point_version, max_version_kind = AnkiVersionCodec.from_manifest_max(manifest.max_point_version)
        max_version: Optional[str] = AnkiVersionCodec.to_str(max_point_version) if max_point_version else None
        return Manifest(manifest.package, manifest.name, list(manifest.conflicts), manifest.min_point_version,
                        manifest.max_point_version, manifest.homepage, manifest.mod, min_version, max_version,
                        str(max_version_kind))

    @staticmethod
    def __forum(addon: AddonInfo) -> Optional[Forum]:
        if not addon or not addon.forum:
            return None
        anki_forum_url: Optional[str] = addon.forum.anki_forum_url
        slug: Optional[str] = addon.forum.topic_slug
        topic_id: Optional[int] = addon.forum.topic_id
        last_posted_at: Optional[str] = str(addon.forum.last_posted_at) if addon.forum.last_posted_at else None
        posts_count: Optional[int] = addon.forum.posts_count
        return Forum(anki_forum_url, slug, topic_id, last_posted_at, posts_count)

    @staticmethod
    def __ai(addon: AddonInfo) -> Optional[Ai]:
        if not addon.ai:
            return None
        return Ai(addon.ai.summary, addon.ai.model, addon.ai.tags)

    @staticmethod
    def __branches(addon: AddonInfo) -> list[Branch]:
        return [Branch(branch.min_anki_version, branch.max_anki_version, str(branch.updated), branch.min_point_version,
                       branch.max_point_version, str(branch.max_version_kind))
                for branch in addon.page.branches]
