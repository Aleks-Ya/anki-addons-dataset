import json
from datetime import datetime
from pathlib import Path
from typing import Any

from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId, GitHubRepo, GithubUserName, \
    GithubRepoName, LanguageName, GithubInfo, AddonPage, Aggregation
from anki_addons_dataset.common.working_dir import VersionDir
from anki_addons_dataset.exporter.json.json_exporter import JsonExporter


def test_export_addon_infos(note_size_addon_id: AddonId, version_dir: VersionDir):
    addon_infos: list[AddonInfo] = [
        AddonInfo(
            header=AddonHeader(note_size_addon_id, "NoteSize", "https://ankiweb.net/shared/info/1188705668",
                               4, "2023-03-15", "1.0.0"),
            page=AddonPage(
                like_number=0,
                dislike_number=0,
                versions=[],
                other_links=[],
                anki_forum_url=None
            ),
            github=GithubInfo(
                github_links=[],
                github_repo=GitHubRepo(GithubUserName("John"), GithubRepoName("app")),
                languages=[LanguageName("Python"), LanguageName("Rust")],
                stars=3,
                last_commit=datetime(2023, 3, 15, 12, 0, 0, 0),
                action_count=5,
                tests_count=7
            ))
    ]
    final_dir: Path = version_dir.get_final_dir()
    exporter: JsonExporter = JsonExporter(final_dir)
    exporter.export_addon_infos(addon_infos)

    act_file: Path = final_dir / "json" / "data.json"
    act_json: dict[str, Any] = json.loads(act_file.read_text())
    assert act_json == [{'addon_page': 'https://ankiweb.net/shared/info/1188705668',
                         'anki_forum_url': None,
                         'dislikes': 0,
                         'github': {'action_count': 5,
                                    'languages': ['Python', 'Rust'],
                                    'last_commit': '2023-03-15T12:00:00',
                                    'links': [],
                                    'repo': 'app',
                                    'stars': 3,
                                    'tests_count': 7,
                                    'user': 'John'},
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
