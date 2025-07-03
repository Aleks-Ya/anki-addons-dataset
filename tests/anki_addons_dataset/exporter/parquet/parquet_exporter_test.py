from datetime import datetime
from pathlib import Path

import pandas
from pandas import DataFrame
import pandas.testing as pdt

from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId, GitHubRepo, GithubUserName, \
    GithubRepoName, LanguageName, GithubInfo, AddonPage, Aggregation
from anki_addons_dataset.common.working_dir import VersionDir
from anki_addons_dataset.exporter.parquet.parquet_exporter import ParquetExporter


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
    exporter: ParquetExporter = ParquetExporter(final_dir)
    exporter.export_addon_infos(addon_infos)

    act_file: Path = final_dir / "parquet" / "data.parquet"
    act_df: DataFrame = pandas.read_parquet(act_file)
    exp_df: DataFrame = DataFrame(
        [{
            'id': 1188705668,
            'name': 'NoteSize',
            'addon_page': 'https://ankiweb.net/shared/info/1188705668',
            'rating': 4,
            'update_date': '2023-03-15',
            'versions_str': '1.0.0',
            'versions': [],
            'anki_forum_url': None,
            'github': {'action_count': 5,
                       'languages': ['Python', 'Rust'],
                       'last_commit': '2023-03-15T12:00:00',
                       'links': [],
                       'repo': 'app',
                       'stars': 3,
                       'tests_count': 7,
                       'user': 'John'},
            'links': [],
            'likes': 0,
            'dislikes': 0
        }]
    )
    pdt.assert_frame_equal(act_df, exp_df)


def test_export_aggregation(version_dir: VersionDir):
    aggregation: Aggregation = Aggregation(addon_number=5,
                                           addon_with_github_number=4,
                                           addon_with_anki_forum_page_number=3,
                                           addon_with_unit_tests_number=2)
    final_dir: Path = version_dir.get_final_dir()
    exporter: ParquetExporter = ParquetExporter(final_dir)
    exporter.export_aggregation(aggregation)

    act_file: Path = final_dir / "parquet" / "aggregation.parquet"
    act_df: DataFrame = pandas.read_parquet(act_file)
    exp_df: DataFrame = DataFrame(
        [{'addon_number': 5,
          'addon_with_github_number': 4,
          'addon_with_anki_forum_page_number': 3,
          'addon_with_unit_tests_number': 2}]
    )
    pdt.assert_frame_equal(act_df, exp_df)
