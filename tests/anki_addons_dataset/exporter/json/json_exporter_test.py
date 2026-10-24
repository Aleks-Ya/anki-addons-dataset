import json
from datetime import date
from dataclasses import replace
from pathlib import Path
from typing import Any, Optional

from anki_addons_dataset.common.data_types import Aggregation, AddonInfos, AddonInfo, AnkiForumInfo, PostsCount, \
    DatasetSnapshotMetadata, RawMetadata, AddonManifest, SpdxLicense, Topic, DependencyName, LanguageName, URL, GithubReadme, \
    AiTagDefinition, AiTag, AiTagGroup, PageLink, PageLinkSection, AnkiRelease, AnkiVersion, AnkiPointVersion, \
    AddonId, ForkRelation, ForkEvidence, ReviewRow, ReviewVote
from anki_addons_dataset.common.working_dir import SnapshotDir
from anki_addons_dataset.exporter.json.json_exporter import JsonExporter


def test_export_addon_infos(json_exporter: JsonExporter, snapshot_dir: SnapshotDir, addon_infos: AddonInfos,
                            dataset_snapshot_metadata: DatasetSnapshotMetadata, raw_metadata: RawMetadata):
    json_exporter.export_addon_infos(addon_infos, dataset_snapshot_metadata, raw_metadata)

    act_file: Path = snapshot_dir.get_final_dir() / "json" / "data.json"
    act_json: dict[str, Any] = json.loads(act_file.read_text())
    assert act_json == [{'id': 1188705668,
                         'anki_web': {'addon_page_url': 'https://ankiweb.net/shared/info/1188705668',
                                      'addon_page_content': '<html><body><h1>Sample addon page content</h1></body></html>',
                                      'contact_author_url': None,
                                      'ai_declaration_markers': ['chatgpt'],
                                      'description': 'Sample addon description for full text search',
                                      'description_language': None,
                                      'description_language_confidence': None,
                                      'description_html': '<p>Sample addon <b>description</b> for full text search</p>',
                                      'description_pre_wrap': True,
                                      'other_items_count': 2,
                                      'anki_version': '25.09.2~',
                                      'anki_point_version': 250902,
                                      'anki_version_kind': 'tested',
                                      'branches': [{'max_version': '25.09.2+',
                                                    'min_version': '24.04.1',
                                                    'updated': '2023-03-15',
                                                    'min_point_version': 240401,
                                                    'max_point_version': 250902,
                                                    'max_version_kind': 'tested'}],
                                      'dislikes': 0,
                                      'likes': 0,
                                      'links': [],
                                      'title': 'NoteSize',
                                      'rating': 4,
                                      'update_date': '2023-03-15'},
                         'github': {'action_count': 5,
                                    'languages': ['Python', 'Rust'],
                                    'last_commit': '2023-03-15T12:00:00',
                                    'links': [],
                                    'repo': 'app',
                                    'stars': 3,
                                    'tests_count': 7,
                                    'user': 'John',
                                    'license': None,
                                    'forks': None,
                                    'open_issues': None,
                                    'size_kb': None,
                                    'topics': [],
                                    'repo_description': None,
                                    'homepage': None,
                                    'archived': None,
                                    'pushed_at': None,
                                    'created_at': None,
                                    'primary_language': None,
                                    'language_bytes': [],
                                    'manifest': None,
                                    'dependencies': [],
                                    'readme': None,
                                    'ai_tooling_markers': ['claude-code', 'cursor'], 'repo_source': None,
                                    'fork_source': None},
                         'forum': {'anki_forum_url': 'https://forums.ankiweb.net/t/note-size-addon-support/46001',
                                   'topic_slug': 'note-size-addon-support',
                                   'topic_id': 46001,
                                   'last_posted_at': '2023-09-10 12:00:00+00:00',
                                   'posts_count': 42, 'topic_source': 'contact_author'},
                         'ai': {'summary': 'Shows the size of the collection and of individual notes.',
                                'model': 'test-model',
                                'tags': ['statistics']},
                         'author': {'id': 1188705668, 'addon_count': 3},
                         'forked_from': None,
                         'forks': []
                         }]


def test_export_addon_infos_empty_forum(json_exporter: JsonExporter, snapshot_dir: SnapshotDir, addon_info: AddonInfo,
                                        dataset_snapshot_metadata: DatasetSnapshotMetadata, raw_metadata: RawMetadata):
    forum: Optional[AnkiForumInfo] = None
    addon_info.forum = forum
    addon_infos: AddonInfos = AddonInfos([addon_info])

    json_exporter.export_addon_infos(addon_infos, dataset_snapshot_metadata, raw_metadata)

    act_file: Path = snapshot_dir.get_final_dir() / "json" / "data.json"
    act_json: dict[str, Any] = json.loads(act_file.read_text())
    assert act_json == [{'id': 1188705668,
                         'anki_web': {'addon_page_url': 'https://ankiweb.net/shared/info/1188705668',
                                      'addon_page_content': '<html><body><h1>Sample addon page content</h1></body></html>',
                                      'contact_author_url': None,
                                      'ai_declaration_markers': ['chatgpt'],
                                      'description': 'Sample addon description for full text search',
                                      'description_language': None,
                                      'description_language_confidence': None,
                                      'description_html': '<p>Sample addon <b>description</b> for full text search</p>',
                                      'description_pre_wrap': True,
                                      'other_items_count': 2,
                                      'anki_version': '25.09.2~',
                                      'anki_point_version': 250902,
                                      'anki_version_kind': 'tested',
                                      'branches': [{'max_version': '25.09.2+',
                                                    'min_version': '24.04.1',
                                                    'updated': '2023-03-15',
                                                    'min_point_version': 240401,
                                                    'max_point_version': 250902,
                                                    'max_version_kind': 'tested'}],
                                      'dislikes': 0,
                                      'likes': 0,
                                      'links': [],
                                      'title': 'NoteSize',
                                      'rating': 4,
                                      'update_date': '2023-03-15'},
                         'github': {'action_count': 5,
                                    'languages': ['Python', 'Rust'],
                                    'last_commit': '2023-03-15T12:00:00',
                                    'links': [],
                                    'repo': 'app',
                                    'stars': 3,
                                    'tests_count': 7,
                                    'user': 'John',
                                    'license': None,
                                    'forks': None,
                                    'open_issues': None,
                                    'size_kb': None,
                                    'topics': [],
                                    'repo_description': None,
                                    'homepage': None,
                                    'archived': None,
                                    'pushed_at': None,
                                    'created_at': None,
                                    'primary_language': None,
                                    'language_bytes': [],
                                    'manifest': None,
                                    'dependencies': [],
                                    'readme': None,
                                    'ai_tooling_markers': ['claude-code', 'cursor'], 'repo_source': None,
                                    'fork_source': None},
                         'forum': None,
                         'ai': {'summary': 'Shows the size of the collection and of individual notes.',
                                'model': 'test-model',
                                'tags': ['statistics']},
                         'author': {'id': 1188705668, 'addon_count': 3},
                         'forked_from': None,
                         'forks': []}]


def test_export_addon_infos_empty_posts_count(json_exporter: JsonExporter, snapshot_dir: SnapshotDir,
                                              addon_info: AddonInfo, dataset_snapshot_metadata: DatasetSnapshotMetadata,
                                              raw_metadata: RawMetadata):
    posts_count: Optional[PostsCount] = None
    addon_info.forum.posts_count = posts_count
    addon_infos: AddonInfos = AddonInfos([addon_info])

    json_exporter.export_addon_infos(addon_infos, dataset_snapshot_metadata, raw_metadata)

    act_file: Path = snapshot_dir.get_final_dir() / "json" / "data.json"
    act_json: dict[str, Any] = json.loads(act_file.read_text())
    assert act_json == [{'id': 1188705668,
                         'anki_web': {'addon_page_url': 'https://ankiweb.net/shared/info/1188705668',
                                      'addon_page_content': '<html><body><h1>Sample addon page content</h1></body></html>',
                                      'contact_author_url': None,
                                      'ai_declaration_markers': ['chatgpt'],
                                      'description': 'Sample addon description for full text search',
                                      'description_language': None,
                                      'description_language_confidence': None,
                                      'description_html': '<p>Sample addon <b>description</b> for full text search</p>',
                                      'description_pre_wrap': True,
                                      'other_items_count': 2,
                                      'anki_version': '25.09.2~',
                                      'anki_point_version': 250902,
                                      'anki_version_kind': 'tested',
                                      'branches': [{'max_version': '25.09.2+',
                                                    'min_version': '24.04.1',
                                                    'updated': '2023-03-15',
                                                    'min_point_version': 240401,
                                                    'max_point_version': 250902,
                                                    'max_version_kind': 'tested'}],
                                      'dislikes': 0,
                                      'likes': 0,
                                      'links': [],
                                      'title': 'NoteSize',
                                      'rating': 4,
                                      'update_date': '2023-03-15'},
                         'github': {'action_count': 5,
                                    'languages': ['Python', 'Rust'],
                                    'last_commit': '2023-03-15T12:00:00',
                                    'links': [],
                                    'repo': 'app',
                                    'stars': 3,
                                    'tests_count': 7,
                                    'user': 'John',
                                    'license': None,
                                    'forks': None,
                                    'open_issues': None,
                                    'size_kb': None,
                                    'topics': [],
                                    'repo_description': None,
                                    'homepage': None,
                                    'archived': None,
                                    'pushed_at': None,
                                    'created_at': None,
                                    'primary_language': None,
                                    'language_bytes': [],
                                    'manifest': None,
                                    'dependencies': [],
                                    'readme': None,
                                    'ai_tooling_markers': ['claude-code', 'cursor'], 'repo_source': None,
                                    'fork_source': None},
                         'forum': {'anki_forum_url': 'https://forums.ankiweb.net/t/note-size-addon-support/46001',
                                   'topic_slug': 'note-size-addon-support',
                                   'topic_id': 46001,
                                   'last_posted_at': '2023-09-10 12:00:00+00:00',
                                   'posts_count': None, 'topic_source': 'contact_author'},
                         'ai': {'summary': 'Shows the size of the collection and of individual notes.',
                                'model': 'test-model',
                                'tags': ['statistics']},
                         'author': {'id': 1188705668, 'addon_count': 3},
                         'forked_from': None,
                         'forks': []}]


def test_export_addon_infos_empty_last_posted_at(json_exporter: JsonExporter, snapshot_dir: SnapshotDir,
                                                 addon_info: AddonInfo,
                                                 dataset_snapshot_metadata: DatasetSnapshotMetadata,
                                                 raw_metadata: RawMetadata):
    addon_info.forum.last_posted_at = None
    addon_infos: AddonInfos = AddonInfos([addon_info])

    json_exporter.export_addon_infos(addon_infos, dataset_snapshot_metadata, raw_metadata)

    act_file: Path = snapshot_dir.get_final_dir() / "json" / "data.json"
    act_json: dict[str, Any] = json.loads(act_file.read_text())
    assert act_json[0]['forum'] == {'anki_forum_url': 'https://forums.ankiweb.net/t/note-size-addon-support/46001',
                                    'topic_slug': 'note-size-addon-support',
                                    'topic_id': 46001,
                                    'last_posted_at': None,
                                    'posts_count': 42, 'topic_source': 'contact_author'}


def test_export_addon_infos_with_enrichment_fields(json_exporter: JsonExporter, snapshot_dir: SnapshotDir,
                                                   addon_info: AddonInfo,
                                                   dataset_snapshot_metadata: DatasetSnapshotMetadata,
                                                   raw_metadata: RawMetadata):
    # Populates every enrichment field so the exported JSON is validated against schema.json with real data.
    assert addon_info.github is not None
    addon_info.github.license = SpdxLicense("MIT")
    addon_info.github.forks = 4
    addon_info.github.topics = [Topic("anki")]
    addon_info.github.homepage = URL("https://example.com")
    addon_info.github.archived = False
    addon_info.github.language_bytes = {LanguageName("Python"): 5, LanguageName("Rust"): 2}
    addon_info.github.primary_language = LanguageName("Python")
    addon_info.github.manifest = AddonManifest(package="note_size", name="Note Size", conflicts=["123"],
                                               min_point_version=45, max_point_version=-250900,
                                               homepage="https://example.com", mod=1678900000)
    addon_info.github.dependencies = [DependencyName("requests")]
    addon_info.github.readme = GithubReadme("# NoteSize")
    addon_info.page.links = [
        PageLink(URL("https://forums.ankiweb.net/t/support/1"), PageLinkSection.DESCRIPTION, 2, ["Forum", "Support"]),
        PageLink(URL("https://github.com/u/r/issues"), PageLinkSection.CONTACT_AUTHOR, 1, ["Contact Author"])]

    json_exporter.export_addon_infos(AddonInfos([addon_info]), dataset_snapshot_metadata, raw_metadata)

    act_file: Path = snapshot_dir.get_final_dir() / "json" / "data.json"
    act_json: dict[str, Any] = json.loads(act_file.read_text())[0]
    assert act_json["anki_web"]["links"] == [
        {"url": "https://forums.ankiweb.net/t/support/1", "section": "description", "count": 2,
         "texts": ["Forum", "Support"]},
        {"url": "https://github.com/u/r/issues", "section": "contact_author", "count": 1, "texts": ["Contact Author"]}]
    assert act_json["anki_web"]["contact_author_url"] == "https://github.com/u/r/issues"
    github: dict[str, Any] = act_json["github"]
    assert github["license"] == "MIT"
    assert github["topics"] == ["anki"]
    assert github["primary_language"] == "Python"
    assert github["language_bytes"] == [{"name": "Python", "bytes": 5}, {"name": "Rust", "bytes": 2}]
    assert github["manifest"]["package"] == "note_size"
    assert github["manifest"]["min_version"] == "2.1.45"
    assert github["manifest"]["max_version"] == "25.09"
    assert github["manifest"]["max_version_kind"] == "hard"
    assert github["dependencies"] == ["requests"]
    assert github["readme"] == "# NoteSize"



def test_export_addon_infos_one_parent_with_several_forks(json_exporter: JsonExporter, snapshot_dir: SnapshotDir,
                                                          addon_info: AddonInfo,
                                                          dataset_snapshot_metadata: DatasetSnapshotMetadata,
                                                          raw_metadata: RawMetadata):
    def addon(addon_id: int, forked_from: Optional[ForkRelation]) -> AddonInfo:
        return replace(addon_info, header=replace(addon_info.header, id=AddonId(addon_id)), forked_from=forked_from)

    json_exporter.export_addon_infos(AddonInfos([
        addon(10, None),
        addon(20, ForkRelation(AddonId(10), ForkEvidence.GITHUB_FORK)),
        addon(30, ForkRelation(AddonId(10), ForkEvidence.AI))]), dataset_snapshot_metadata, raw_metadata)

    act_file: Path = snapshot_dir.get_final_dir() / "json" / "data.json"
    act_json: list[dict[str, Any]] = json.loads(act_file.read_text())
    assert [(item["id"], item["forked_from"], item["forks"]) for item in act_json] == [
        (10, None, [20, 30]),
        (20, {"id": 10, "evidence": "github_fork"}, []),
        (30, {"id": 10, "evidence": "ai"}, [])]

def test_export_aggregation(json_exporter: JsonExporter, snapshot_dir: SnapshotDir,
                            dataset_snapshot_metadata: DatasetSnapshotMetadata, raw_metadata: RawMetadata):
    aggregation: Aggregation = Aggregation(addon_number=5,
                                           addon_with_github_number=4,
                                           addon_with_anki_forum_page_number=3,
                                           addon_with_unit_tests_number=2,
                                           author_number=1)
    json_exporter.export_aggregation(aggregation, dataset_snapshot_metadata, raw_metadata)

    act_file: Path = snapshot_dir.get_final_dir() / "json" / "aggregation.json"
    act_json: dict[str, Any] = json.loads(act_file.read_text())
    assert act_json == {'addon_number': 5,
                        'addon_with_anki_forum_page_number': 3,
                        'addon_with_github_number': 4,
                        'addon_with_unit_tests_number': 2,
          'author_number': 1}


def test_export_tags(json_exporter: JsonExporter, snapshot_dir: SnapshotDir,
                     dataset_snapshot_metadata: DatasetSnapshotMetadata, raw_metadata: RawMetadata):
    tags: list[AiTagDefinition] = [AiTagDefinition(AiTag("statistics"), AiTagGroup("function"), "Graphs"),
                                   AiTagDefinition(AiTag("paid"), AiTagGroup("status"), "Patreon-only")]
    json_exporter.export_tags(tags, dataset_snapshot_metadata, raw_metadata)

    act_file: Path = snapshot_dir.get_final_dir() / "json" / "tags.json"
    act_json: list[dict[str, Any]] = json.loads(act_file.read_text())
    assert act_json == [{'name': 'statistics', 'group': 'function', 'description': 'Graphs'},
                        {'name': 'paid', 'group': 'status', 'description': 'Patreon-only'}]


def test_export_anki_versions(json_exporter: JsonExporter, snapshot_dir: SnapshotDir,
                              dataset_snapshot_metadata: DatasetSnapshotMetadata, raw_metadata: RawMetadata):
    anki_versions: list[AnkiRelease] = [AnkiRelease(AnkiVersion("25.09.2"), AnkiPointVersion(250902)),
                                        AnkiRelease(AnkiVersion("2.1.66"), AnkiPointVersion(66))]
    json_exporter.export_anki_versions(anki_versions, dataset_snapshot_metadata, raw_metadata)

    act_file: Path = snapshot_dir.get_final_dir() / "json" / "anki_versions.json"
    act_json: list[dict[str, Any]] = json.loads(act_file.read_text())
    assert act_json == [{'version': '25.09.2', 'point_version': 250902},
                        {'version': '2.1.66', 'point_version': 66}]


def test_export_reviews(json_exporter: JsonExporter, snapshot_dir: SnapshotDir):
    reviews: list[ReviewRow] = [
        ReviewRow(AddonId(1188705668), date(2026, 7, 5), ReviewVote.DISLIKE, "Produces errors", None),
        ReviewRow(AddonId(1188705668), date(2025, 6, 6), ReviewVote.LIKE, "Works\nfine", "Thank you!")]
    json_exporter.export_reviews(reviews)

    act_file: Path = snapshot_dir.get_final_dir() / "json" / "reviews.json"
    act_json: list[dict[str, Any]] = json.loads(act_file.read_text())
    assert act_json == [
        {'addon_id': 1188705668, 'date': '2026-07-05', 'vote': 'dislike', 'text': 'Produces errors',
         'author_reply': None},
        {'addon_id': 1188705668, 'date': '2025-06-06', 'vote': 'like', 'text': 'Works\nfine',
         'author_reply': 'Thank you!'}]
