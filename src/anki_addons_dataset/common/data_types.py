from datetime import datetime, date
from typing import NewType, Optional
from dataclasses import dataclass, field
from enum import StrEnum

SnapshotDate = NewType("SnapshotDate", date)
ReportDate = NewType("ReportDate", datetime)
ScriptVersion = NewType("ScriptVersion", str)
AddonId = NewType("AddonId", int)
AddonTitle = NewType("AddonTitle", str)
AddonRating = NewType("AddonRating", int)
AddonDescription = NewType("AddonDescription", str)
UpdateDate = NewType("UpdateDate", date)
URL = NewType("URL", str)
GithubRepoName = NewType("GithubRepoName", str)
GithubUserName = NewType("GithubUserName", str)
GithubRepoId = NewType("GithubRepoId", str)
GithubReadme = NewType("GithubReadme", str)
LanguageName = NewType("LanguageName", str)
LanguageCode = NewType("LanguageCode", str)
HtmlStr = NewType("HtmlStr", str)
TopicSlug = NewType("TopicSlug", str)
TopicId = NewType("TopicId", int)
LastPostedAt = NewType("LastPostedAt", datetime)
PostsCount = NewType("PostsCount", int)
HuggingFaceFolder = NewType("HuggingFaceFolder", str)
AnkiVersion = NewType("AnkiVersion", str)
AnkiPointVersion = NewType("AnkiPointVersion", int)
SpdxLicense = NewType("SpdxLicense", str)
DependencyName = NewType("DependencyName", str)
Topic = NewType("Topic", str)
PageLoadTimeout = NewType("PageLoadTimeout", int)
ElementWaitTimeout = NewType("ElementWaitTimeout", int)
AiSummary = NewType("AiSummary", str)
AiTag = NewType("AiTag", str)
AiTagGroup = NewType("AiTagGroup", str)
AiModel = NewType("AiModel", str)
AuthorId = NewType("AuthorId", int)


class AnkiVersionKind(StrEnum):
    HARD = "hard"
    TESTED = "tested"
    OPEN = "open"
    UNKNOWN = "unknown"


class PageLinkSection(StrEnum):
    DESCRIPTION = "description"
    CONTACT_AUTHOR = "contact_author"


class GithubRepoSource(StrEnum):
    OVERRIDE = "override"
    CONTACT_AUTHOR = "contact_author"
    SELF_REFERENCE = "self_reference"
    AI = "ai"
    MOST_LINKED = "most_linked"


class AnkiForumTopicSource(StrEnum):
    OVERRIDE = "override"
    CONTACT_AUTHOR = "contact_author"
    AI = "ai"
    MOST_LINKED = "most_linked"
    TITLE_MATCH = "title_match"


class ForkEvidence(StrEnum):
    GITHUB_FORK = "github_fork"
    AI = "ai"
    OVERRIDE = "override"


class ReviewVote(StrEnum):
    LIKE = "like"
    DISLIKE = "dislike"


@dataclass(frozen=True)
class AddonHeader:
    id: AddonId
    title: AddonTitle
    addon_page_url: URL
    rating: AddonRating
    update_date: UpdateDate
    anki_version: AnkiVersion
    anki_point_version: Optional[AnkiPointVersion] = None
    anki_version_kind: AnkiVersionKind = AnkiVersionKind.UNKNOWN


@dataclass(frozen=True)
class GithubUser:
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


@dataclass(frozen=True)
class GithubLink:
    url: URL
    user: GithubUser
    repo: Optional[GithubRepo]


@dataclass(frozen=True)
class AddonManifest:
    """Parsed Anki addon `manifest.json` (the metadata Anki ships inside each add-on package)."""
    package: Optional[str] = None
    name: Optional[str] = None
    conflicts: list[str] = field(default_factory=list)
    min_point_version: Optional[AnkiPointVersion] = None
    max_point_version: Optional[AnkiPointVersion] = None
    homepage: Optional[URL] = None
    mod: Optional[int] = None


@dataclass(frozen=True)
class GithubReleaseAsset:
    name: str
    size: int
    download_count: int


@dataclass(frozen=True)
class GithubRelease:
    tag_name: str
    name: Optional[str]
    published_at: Optional[datetime]
    prerelease: bool
    assets: list[GithubReleaseAsset]


@dataclass(frozen=True)
class GithubContributor:
    login: GithubUserName
    contributions: int


@dataclass(frozen=True)
class GithubIssueHistory:
    has_issues_enabled: bool
    open_issue_count: int
    closed_issue_count: int
    open_pr_count: int
    closed_pr_count: int
    merged_pr_count: int
    last_issue_closed_at: Optional[datetime]
    median_first_response_hours: Optional[float]
    first_response_sample: int
    outside_prs_merged: int
    outside_prs_decided: int


@dataclass(frozen=True)
class GithubInfo:
    github_links: list[GithubLink]
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
    readme: Optional[GithubReadme] = None
    ai_tooling_markers: list[str] = field(default_factory=list)
    repo_source: Optional[GithubRepoSource] = None
    fork_source: Optional[GithubRepo] = None
    releases: Optional[list[GithubRelease]] = None
    contributors: Optional[list[GithubContributor]] = None
    weekly_commits: Optional[list[int]] = None
    issue_history: Optional[GithubIssueHistory] = None


@dataclass(frozen=True)
class AddonBranch:
    min_anki_version: AnkiVersion
    max_anki_version: Optional[AnkiVersion]
    updated: date
    min_point_version: Optional[AnkiPointVersion] = None
    max_point_version: Optional[AnkiPointVersion] = None
    max_version_kind: AnkiVersionKind = AnkiVersionKind.UNKNOWN


@dataclass(frozen=True)
class PageLink:
    url: URL
    section: PageLinkSection
    count: int = 1
    texts: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AddonReview:
    vote: ReviewVote
    date: date
    text: str
    author_reply: Optional[str] = None


@dataclass(frozen=True)
class AddonPage:
    content: HtmlStr
    like_number: int
    dislike_number: int
    branches: list[AddonBranch]
    links: list[PageLink]
    description: AddonDescription = AddonDescription("")
    ai_declaration_markers: list[str] = field(default_factory=list)
    description_language: Optional[LanguageCode] = None
    description_language_confidence: Optional[float] = None
    description_html: Optional[HtmlStr] = None
    description_pre_wrap: bool = False
    other_items_count: Optional[int] = None
    reviews: list[AddonReview] = field(default_factory=list)
    package_size_kb: Optional[int] = None

    @property
    def contact_author_url(self) -> Optional[URL]:
        for link in self.links:
            if link.section == PageLinkSection.CONTACT_AUTHOR:
                return link.url
        return None


@dataclass(frozen=True)
class AnkiForumInfo:
    anki_forum_url: Optional[URL]
    topic_slug: Optional[TopicSlug]
    topic_id: Optional[TopicId]
    last_posted_at: Optional[LastPostedAt]
    posts_count: Optional[PostsCount]
    topic_source: Optional[AnkiForumTopicSource] = None


@dataclass(frozen=True)
class AnkiForumPost:
    number: int
    username: str
    text: str
    links: list[URL]


@dataclass(frozen=True)
class AnkiForumTopicContent:
    title: str
    created_by: Optional[str]
    posts_count: int
    posts: list[AnkiForumPost]


@dataclass(frozen=True)
class AnkiForumCategoryTopic:
    id: TopicId
    slug: TopicSlug
    title: str
    posts_count: PostsCount


@dataclass(frozen=True)
class AiInfo:
    summary: Optional[AiSummary] = None
    model: Optional[AiModel] = None
    tags: Optional[list[AiTag]] = None
    fork_of: Optional[AddonId] = None


@dataclass(frozen=True)
class AiTagDefinition:
    name: AiTag
    group: AiTagGroup
    description: str


@dataclass(frozen=True)
class AnkiRelease:
    version: AnkiVersion
    point_version: AnkiPointVersion
    release_date: Optional[date] = None


@dataclass(frozen=True)
class ReviewRow:
    addon_id: AddonId
    date: date
    vote: ReviewVote
    text: str
    author_reply: Optional[str]


@dataclass(frozen=True)
class AddonPackage:
    file_name: str
    min_point_version: AnkiPointVersion
    updated: date
    size_bytes: int
    manifest_json: Optional[str]
    config_json: Optional[str]
    file_count: int
    uncompressed_bytes: int
    python_file_count: int
    python_lines: int
    files: list[str]
    language_bytes: dict[LanguageName, int]


@dataclass(frozen=True)
class AddonPackages:
    branches: list[AddonPackage]


@dataclass(frozen=True)
class PackageRow:
    addon_id: AddonId
    file_name: str
    min_point_version: AnkiPointVersion
    updated: date
    size_bytes: int
    manifest_json: Optional[str]
    config_json: Optional[str]
    file_count: int
    uncompressed_bytes: int
    python_file_count: int
    python_lines: int
    files: list[str]
    language_bytes: dict[LanguageName, int]


@dataclass(frozen=True)
class AuthorInfo:
    author_id: AuthorId
    addon_ids: list[AddonId]


@dataclass(frozen=True)
class ForkRelation:
    addon_id: AddonId
    evidence: ForkEvidence


@dataclass(frozen=True)
class AddonInfo:
    header: AddonHeader
    page: AddonPage
    github: Optional[GithubInfo]
    forum: Optional[AnkiForumInfo]
    ai: Optional[AiInfo] = None
    author: Optional[AuthorInfo] = None
    forked_from: Optional[ForkRelation] = None
    package: Optional[AddonPackages] = None


AddonInfos = NewType("AddonInfos", list[AddonInfo])


@dataclass(frozen=True)
class RawMetadata:
    start_timestamp: Optional[datetime] = None
    finish_timestamp: Optional[datetime] = None
    script_version: Optional[ScriptVersion] = None


@dataclass(frozen=True)
class DatasetSnapshotMetadata:
    data_collection_date: SnapshotDate
    report_generation_date: ReportDate
    script_version: ScriptVersion

    def __str__(self) -> str:
        return (f"DatasetSnapshotMetadata("
                f"data_collection_date={self.data_collection_date.isoformat()}, "
                f"report_generation_date={self.report_generation_date.isoformat(sep=' ')}, "
                f"script_version={self.script_version})")
