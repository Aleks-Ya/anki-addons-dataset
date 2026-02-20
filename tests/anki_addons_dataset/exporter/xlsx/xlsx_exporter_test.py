from datetime import datetime
from pathlib import Path

import pandas
from pandas import DataFrame
import pandas.testing as pdt

from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId, GitHubRepo, LanguageName, GithubInfo, \
    AddonPage, Aggregation, AddonInfos, AnkiForumInfo, TopicSlug, TopicId, \
    LastPostedAt, URL
from anki_addons_dataset.common.working_dir import VersionDir
from anki_addons_dataset.exporter.xlsx.xlsx_exporter import XlsxExporter


def test_export_addon_infos(note_size_addon_id: AddonId, version_dir: VersionDir, topic_slug: TopicSlug,
                            topic_id: TopicId, last_posted_at: LastPostedAt, github_repo: GitHubRepo):
    addon_infos: AddonInfos = AddonInfos([
        AddonInfo(
            header=AddonHeader(
                id=note_size_addon_id,
                name="NoteSize",
                addon_page="https://ankiweb.net/shared/info/1188705668",
                rating=4,
                update_date="2023-03-15",
                versions="1.0.0"
            ),
            page=AddonPage(
                like_number=0,
                dislike_number=0,
                versions=[],
                other_links=[],
                anki_forum_url=URL("https://forums.ankiweb.net/t/note-size-addon-support/46001")
            ),
            github=GithubInfo(
                github_links=[],
                github_repo=github_repo,
                languages=[LanguageName("Python"), LanguageName("Rust")],
                stars=3,
                last_commit=datetime(2023, 3, 15, 12, 0, 0, 0),
                action_count=5,
                tests_count=7
            ),
            forum=AnkiForumInfo(
                topic_slug=topic_slug,
                topic_id=topic_id,
                last_posted_at=last_posted_at
            )
        )
    ])
    final_dir: Path = version_dir.get_final_dir()
    exporter: XlsxExporter = XlsxExporter(final_dir)
    exporter.export_addon_infos(addon_infos)

    act_file: Path = final_dir / "xlsx" / "data.xlsx"
    act_df: DataFrame = pandas.read_excel(act_file)
    exp_file: Path = Path(__file__).parent / "exp_data.xlsx"
    exp_df: DataFrame = pandas.read_excel(exp_file)
    pdt.assert_frame_equal(act_df, exp_df)


def test_export_aggregation(version_dir: VersionDir):
    aggregation: Aggregation = Aggregation(addon_number=5,
                                           addon_with_github_number=4,
                                           addon_with_anki_forum_page_number=3,
                                           addon_with_unit_tests_number=2)
    final_dir: Path = version_dir.get_final_dir()
    exporter: XlsxExporter = XlsxExporter(final_dir)
    exporter.export_aggregation(aggregation)

    act_file: Path = final_dir / "xlsx" / "aggregation.xlsx"
    act_df: DataFrame = pandas.read_excel(act_file)
    exp_file: Path = Path(__file__).parent / "exp_aggregation.xlsx"
    exp_df: DataFrame = pandas.read_excel(exp_file)
    pdt.assert_frame_equal(act_df, exp_df)
