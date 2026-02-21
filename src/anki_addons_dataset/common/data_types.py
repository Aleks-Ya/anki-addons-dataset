from datetime import datetime, date
from typing import NewType, Optional
from dataclasses import dataclass

AddonId = NewType("AddonId", int)
URL = NewType("URL", str)
GithubRepoName = NewType("GithubRepoName", str)
GithubUserName = NewType("GithubUserName", str)
GithubRepoId = NewType("GithubRepoId", str)
LanguageName = NewType("LanguageName", str)
HtmlStr = NewType("HtmlStr", str)
TopicSlug = NewType("TopicSlug", str)
TopicId = NewType("TopicId", int)
LastPostedAt = NewType("LastPostedAt", datetime)


@dataclass
class AddonHeader:
    id: AddonId
    name: str
    addon_page: str
    rating: int
    update_date: str
    versions: str


@dataclass
class GitHubUser:
    user_name: GithubUserName

    def get_url(self) -> URL:
        return URL(f"https://github.com/{self.user_name}")


@dataclass(frozen=True)
class GithubRepo:
    user: GithubUserName
    repo_name: GithubRepoName

    def get_id(self) -> GithubRepoId:
        return GithubRepoId(f"{self.user}/{self.repo_name}")

    def get_url(self) -> URL:
        return URL(f"https://github.com/{self.user}/{self.repo_name}")


@dataclass
class GitHubLink:
    url: URL
    user: GitHubUser
    repo: Optional[GithubRepo]


@dataclass
class GithubInfo:
    github_links: list[GitHubLink]
    github_repo: Optional[GithubRepo]
    languages: list[LanguageName]
    stars: int
    last_commit: Optional[datetime]
    action_count: int
    tests_count: int


@dataclass
class Version:
    min_version: str
    max_version: str
    updated: date


@dataclass
class AddonPage:
    like_number: int
    dislike_number: int
    versions: list[Version]
    other_links: list[URL]
    anki_forum_url: Optional[URL]


@dataclass
class AnkiForumInfo:
    topic_slug: TopicSlug
    topic_id: TopicId
    last_posted_at: Optional[LastPostedAt]


@dataclass
class AddonInfo:
    header: AddonHeader
    page: AddonPage
    github: Optional[GithubInfo]
    forum: Optional[AnkiForumInfo]


AddonInfos = NewType("AddonInfos", list[AddonInfo])


@dataclass
class Aggregation:
    addon_number: int
    addon_with_github_number: int
    addon_with_anki_forum_page_number: int
    addon_with_unit_tests_number: int
