import json
from pathlib import Path
from typing import Any, Optional

from anki_addons_dataset.common.data_types import Aggregation, AddonInfos, AddonInfo, AnkiForumInfo, PostsCount, \
    DatasetVersionMetadata, RawMetadata
from anki_addons_dataset.common.working_dir import VersionDir
from anki_addons_dataset.exporter.json.json_exporter import JsonExporter


def test_export_addon_infos(json_exporter: JsonExporter, version_dir: VersionDir, addon_infos: AddonInfos,
                            dataset_version_metadata: DatasetVersionMetadata, raw_metadata: RawMetadata):
    json_exporter.export_addon_infos(addon_infos, dataset_version_metadata, raw_metadata)

    act_file: Path = version_dir.get_final_dir() / "json" / "data.json"
    act_json: dict[str, Any] = json.loads(act_file.read_text())
    assert act_json == [{'addon_page': 'https://ankiweb.net/shared/info/1188705668',
                         'dislikes': 0,
                         'github': {'action_count': 5,
                                    'languages': ['Python', 'Rust'],
                                    'last_commit': '2023-03-15T12:00:00',
                                    'links': [],
                                    'repo': 'app',
                                    'stars': 3,
                                    'tests_count': 7,
                                    'user': 'John'},
                         'forum': {'anki_forum_url': 'https://forums.ankiweb.net/t/note-size-addon-support/46001',
                                   'topic_slug': 'note-size-addon-support',
                                   'topic_id': 46001,
                                   'last_posted_at': '2023-09-10 12:00:00+00:00',
                                   'posts_count': 42},
                         'id': 1188705668,
                         'likes': 0,
                         'links': [],
                         'rating': 4,
                         'name': 'NoteSize',
                         'update_date': '2023-03-15',
                         'versions': [],
                         'versions_str': '1.0.0'}]


def test_export_addon_infos_empty_forum(json_exporter: JsonExporter, version_dir: VersionDir, addon_info: AddonInfo,
                                        dataset_version_metadata: DatasetVersionMetadata, raw_metadata: RawMetadata):
    forum: Optional[AnkiForumInfo] = None
    addon_info.forum = forum
    addon_infos: AddonInfos = AddonInfos([addon_info])

    json_exporter.export_addon_infos(addon_infos, dataset_version_metadata, raw_metadata)

    act_file: Path = version_dir.get_final_dir() / "json" / "data.json"
    act_json: dict[str, Any] = json.loads(act_file.read_text())
    assert act_json == [{'addon_page': 'https://ankiweb.net/shared/info/1188705668',
                         'dislikes': 0,
                         'github': {'action_count': 5,
                                    'languages': ['Python', 'Rust'],
                                    'last_commit': '2023-03-15T12:00:00',
                                    'links': [],
                                    'repo': 'app',
                                    'stars': 3,
                                    'tests_count': 7,
                                    'user': 'John'},
                         'forum': None,
                         'id': 1188705668,
                         'likes': 0,
                         'links': [],
                         'rating': 4,
                         'name': 'NoteSize',
                         'update_date': '2023-03-15',
                         'versions': [],
                         'versions_str': '1.0.0'}]


def test_export_addon_infos_empty_posts_count(json_exporter: JsonExporter, version_dir: VersionDir,
                                              addon_info: AddonInfo, dataset_version_metadata: DatasetVersionMetadata,
                                              raw_metadata: RawMetadata):
    posts_count: Optional[PostsCount] = None
    addon_info.forum.posts_count = posts_count
    addon_infos: AddonInfos = AddonInfos([addon_info])

    json_exporter.export_addon_infos(addon_infos, dataset_version_metadata, raw_metadata)

    act_file: Path = version_dir.get_final_dir() / "json" / "data.json"
    act_json: dict[str, Any] = json.loads(act_file.read_text())
    assert act_json == [{'addon_page': 'https://ankiweb.net/shared/info/1188705668',
                         'dislikes': 0,
                         'github': {'action_count': 5,
                                    'languages': ['Python', 'Rust'],
                                    'last_commit': '2023-03-15T12:00:00',
                                    'links': [],
                                    'repo': 'app',
                                    'stars': 3,
                                    'tests_count': 7,
                                    'user': 'John'},
                         'forum': {'anki_forum_url': 'https://forums.ankiweb.net/t/note-size-addon-support/46001',
                                   'topic_slug': 'note-size-addon-support',
                                   'topic_id': 46001,
                                   'last_posted_at': '2023-09-10 12:00:00+00:00',
                                   'posts_count': None},
                         'id': 1188705668,
                         'likes': 0,
                         'links': [],
                         'rating': 4,
                         'name': 'NoteSize',
                         'update_date': '2023-03-15',
                         'versions': [],
                         'versions_str': '1.0.0'}]


def test_export_aggregation(json_exporter: JsonExporter, version_dir: VersionDir,
                            dataset_version_metadata: DatasetVersionMetadata, raw_metadata: RawMetadata):
    aggregation: Aggregation = Aggregation(addon_number=5,
                                           addon_with_github_number=4,
                                           addon_with_anki_forum_page_number=3,
                                           addon_with_unit_tests_number=2)
    json_exporter.export_aggregation(aggregation, dataset_version_metadata, raw_metadata)

    act_file: Path = version_dir.get_final_dir() / "json" / "aggregation.json"
    act_json: dict[str, Any] = json.loads(act_file.read_text())
    assert act_json == {'addon_number': 5,
                        'addon_with_anki_forum_page_number': 3,
                        'addon_with_github_number': 4,
                        'addon_with_unit_tests_number': 2}
