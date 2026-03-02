import json
from pathlib import Path
from typing import Any

from anki_addons_dataset.common.data_types import Aggregation, AddonInfos
from anki_addons_dataset.common.working_dir import VersionDir
from anki_addons_dataset.exporter.json.json_exporter import JsonExporter


def test_export_addon_infos(version_dir: VersionDir, addon_infos: AddonInfos):
    final_dir: Path = version_dir.get_final_dir()
    exporter: JsonExporter = JsonExporter(final_dir)
    exporter.export_addon_infos(addon_infos)

    act_file: Path = final_dir / "json" / "data.json"
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


def test_export_aggregation(version_dir: VersionDir):
    aggregation: Aggregation = Aggregation(addon_number=5,
                                           addon_with_github_number=4,
                                           addon_with_anki_forum_page_number=3,
                                           addon_with_unit_tests_number=2)
    final_dir: Path = version_dir.get_final_dir()
    exporter: JsonExporter = JsonExporter(final_dir)
    exporter.export_aggregation(aggregation)

    act_file: Path = final_dir / "json" / "aggregation.json"
    act_json: dict[str, Any] = json.loads(act_file.read_text())
    assert act_json == {'addon_number': 5,
                        'addon_with_anki_forum_page_number': 3,
                        'addon_with_github_number': 4,
                        'addon_with_unit_tests_number': 2}
