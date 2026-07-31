from datetime import datetime, date
from typing import NewType, Optional
from dataclasses import dataclass, field

SnapshotDate = NewType("SnapshotDate", date)
ReportDate = NewType("ReportDate", datetime)
ScriptVersion = NewType("ScriptVersion", str)
AddonId = NewType("AddonId", int)
AddonTitle = NewType("AddonTitle", str)
AddonRating = NewType("AddonRating", int)
UpdateDate = NewType("UpdateDate", str)
URL = NewType("URL", str)
GithubRepoName = NewType("GithubRepoName", str)
GithubUserName = NewType("GithubUserName", str)
GithubRepoId = NewType("GithubRepoId", str)
LanguageName = NewType("LanguageName", str)
HtmlStr = NewType("HtmlStr", str)
PlainStr = NewType("PlainStr", str)
TopicSlug = NewType("TopicSlug", str)
TopicId = NewType("TopicId", int)
LastPostedAt = NewType("LastPostedAt", datetime)
PostsCount = NewType("PostsCount", int)
HuggingFaceFolder = NewType("HuggingFaceFolder", str)
AnkiVersion = NewType("AnkiVersion", str)
SpdxLicense = NewType("SpdxLicense", str)
DependencyName = NewType("DependencyName", str)
Topic = NewType("Topic", str)


@dataclass
class AddonHeader:
    id: AddonId
    title: AddonTitle
    addon_page_url: URL
    rating: AddonRating
    update_date: UpdateDate
    anki_version: AnkiVersion


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
class AddonManifest:
    """Parsed Anki addon `manifest.json` (the metadata Anki ships inside each add-on package)."""
    package: Optional[str] = None
    name: Optional[str] = None
    conflicts: list[str] = field(default_factory=list)
    min_point_version: Optional[int] = None
    max_point_version: Optional[int] = None
    homepage: Optional[str] = None
    mod: Optional[int] = None


@dataclass
class GithubInfo:
    github_links: list[GitHubLink]
    github_repo: Optional[GithubRepo]
    languages: list[LanguageName]
    stars: int
    last_commit: Optional[datetime]
    action_count: Optional[int]
    tests_count: Optional[int]
    # Developer-facing enrichment (all optional; populated by GithubEnricher, default-empty elsewhere).
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
    primary_language: Optional[LanguageName] = None
    language_bytes: dict[LanguageName, int] = field(default_factory=dict)
    manifest: Optional[AddonManifest] = None
    dependencies: list[DependencyName] = field(default_factory=list)
    readme: Optional[str] = None


@dataclass
class AddonBranch:
    min_anki_version: AnkiVersion
    max_anki_version: Optional[AnkiVersion]
    updated: date


@dataclass
class AddonPage:
    content: HtmlStr
    like_number: int
    dislike_number: int
    branches: list[AddonBranch]
    other_links: list[URL]
    description: PlainStr = PlainStr("")
    contact_author_url: Optional[URL] = None


@dataclass
class AnkiForumInfo:
    anki_forum_url: Optional[URL]
    topic_slug: Optional[TopicSlug]
    topic_id: Optional[TopicId]
    last_posted_at: Optional[LastPostedAt]
    posts_count: Optional[PostsCount]


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


@dataclass
class RawMetadata:
    start_timestamp: Optional[datetime] = None
    finish_timestamp: Optional[datetime] = None
    script_version: Optional[ScriptVersion] = None


@dataclass
class DatasetSnapshotMetadata:
    data_collection_date: SnapshotDate
    report_generation_date: ReportDate
    script_version: ScriptVersion

    def __str__(self) -> str:
        return (f"DatasetSnapshotMetadata("
                f"data_collection_date={self.data_collection_date.isoformat()}, "
                f"report_generation_date={self.report_generation_date.isoformat(sep=' ')}, "
                f"script_version={self.script_version})")
