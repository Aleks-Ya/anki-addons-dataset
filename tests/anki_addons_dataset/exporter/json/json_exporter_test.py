import json
from pathlib import Path
from typing import Any, Optional

from anki_addons_dataset.common.data_types import Aggregation, AddonInfos, AddonInfo, AnkiForumInfo, PostsCount, \
    DatasetSnapshotMetadata, RawMetadata, AddonManifest, SpdxLicense, Topic, DependencyName, LanguageName, URL
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
                                      'anki_version': '25.09.2~',
                                      'branches': [{'max_version': '25.09.2~',
                                                    'min_version': '24.04.1',
                                                    'updated': '2023-03-15'}],
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
                                    'ai_tooling_markers': ['claude-code', 'cursor']},
                         'forum': {'anki_forum_url': 'https://forums.ankiweb.net/t/note-size-addon-support/46001',
                                   'topic_slug': 'note-size-addon-support',
                                   'topic_id': 46001,
                                   'last_posted_at': '2023-09-10 12:00:00+00:00',
                                   'posts_count': 42}
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
                                      'anki_version': '25.09.2~',
                                      'branches': [{'max_version': '25.09.2~',
                                                    'min_version': '24.04.1',
                                                    'updated': '2023-03-15'}],
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
                                    'ai_tooling_markers': ['claude-code', 'cursor']},
                         'forum': None}]


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
                                      'anki_version': '25.09.2~',
                                      'branches': [{'max_version': '25.09.2~',
                                                    'min_version': '24.04.1',
                                                    'updated': '2023-03-15'}],
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
                                    'ai_tooling_markers': ['claude-code', 'cursor']},
                         'forum': {'anki_forum_url': 'https://forums.ankiweb.net/t/note-size-addon-support/46001',
                                   'topic_slug': 'note-size-addon-support',
                                   'topic_id': 46001,
                                   'last_posted_at': '2023-09-10 12:00:00+00:00',
                                   'posts_count': None}}]


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
                                    'posts_count': 42}


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
                                               min_point_version=45, homepage="https://example.com", mod=1678900000)
    addon_info.github.dependencies = [DependencyName("requests")]
    addon_info.github.readme = "# NoteSize"

    json_exporter.export_addon_infos(AddonInfos([addon_info]), dataset_snapshot_metadata, raw_metadata)

    act_file: Path = snapshot_dir.get_final_dir() / "json" / "data.json"
    github: dict[str, Any] = json.loads(act_file.read_text())[0]["github"]
    assert github["license"] == "MIT"
    assert github["topics"] == ["anki"]
    assert github["primary_language"] == "Python"
    assert github["language_bytes"] == [{"name": "Python", "bytes": 5}, {"name": "Rust", "bytes": 2}]
    assert github["manifest"]["package"] == "note_size"
    assert github["dependencies"] == ["requests"]
    assert github["readme"] == "# NoteSize"


def test_export_aggregation(json_exporter: JsonExporter, snapshot_dir: SnapshotDir,
                            dataset_snapshot_metadata: DatasetSnapshotMetadata, raw_metadata: RawMetadata):
    aggregation: Aggregation = Aggregation(addon_number=5,
                                           addon_with_github_number=4,
                                           addon_with_anki_forum_page_number=3,
                                           addon_with_unit_tests_number=2)
    json_exporter.export_aggregation(aggregation, dataset_snapshot_metadata, raw_metadata)

    act_file: Path = snapshot_dir.get_final_dir() / "json" / "aggregation.json"
    act_json: dict[str, Any] = json.loads(act_file.read_text())
    assert act_json == {'addon_number': 5,
                        'addon_with_anki_forum_page_number': 3,
                        'addon_with_github_number': 4,
                        'addon_with_unit_tests_number': 2}
