from datetime import datetime
from pathlib import Path
from textwrap import dedent

from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId, GitHubRepo, GithubUserName, \
    GithubRepoName, LanguageName, GithubInfo, AddonPage, Aggregation
from anki_addons_dataset.common.working_dir import VersionDir
from anki_addons_dataset.exporter.csv.csv_exporter import CsvExporter


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
    exporter: CsvExporter = CsvExporter(final_dir)
    exporter.export_addon_infos(addon_infos)

    act_file: Path = final_dir / "csv" / "data.csv"
    assert act_file.read_text() == dedent("""\
    ID,Name,Rating,Stars
    1188705668,NoteSize,4,3
    """)


def test_export_aggregation(note_size_addon_id: AddonId, version_dir: VersionDir):
    aggregation: Aggregation = Aggregation(addon_number=5,
                                           addon_with_github_number=4,
                                           addon_with_anki_forum_page_number=3,
                                           addon_with_unit_tests_number=2)
    final_dir: Path = version_dir.get_final_dir()
    exporter: CsvExporter = CsvExporter(final_dir)
    exporter.export_aggregation(aggregation)

    act_file: Path = final_dir / "csv" / "aggregation.csv"
    assert act_file.read_text() == dedent("""\
    Addon number
    5
    """)
