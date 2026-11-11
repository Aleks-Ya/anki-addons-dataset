from datetime import date
from pathlib import Path

import numpy
import pandas
from pandas import DataFrame
import pandas.testing as pdt
import pyarrow
import pyarrow.parquet

from anki_addons_dataset.common.data_types import AddonInfos, DatasetSnapshotMetadata, RawMetadata, \
    AiTagDefinition, AiTag, AiTagGroup, AnkiRelease, AnkiVersion, AnkiPointVersion, ReviewRow, ReviewVote, AddonId, \
    LanguageName, PackageRow, AddonReview, AddonPackage
from anki_addons_dataset.common.working_dir import SnapshotDir
from anki_addons_dataset.exporter.parquet.parquet_exporter import ParquetExporter


def test_export_addon_infos(snapshot_dir: SnapshotDir, addon_infos: AddonInfos,
                            dataset_snapshot_metadata: DatasetSnapshotMetadata, raw_metadata: RawMetadata):
    final_dir: Path = snapshot_dir.get_final_dir()
    exporter: ParquetExporter = ParquetExporter(final_dir)
    exporter.export_addon_infos(addon_infos, dataset_snapshot_metadata, raw_metadata)

    act_file: Path = final_dir / "parquet" / "data.parquet"
    act_df: DataFrame = pandas.read_parquet(act_file)
    exp_df: DataFrame = DataFrame(
        [{
            'id': 1188705668,
            'anki_web': {'addon_page_url': 'https://ankiweb.net/shared/info/1188705668',
                                      'contact_author_url': None,
                         'ai_declaration_markers': ['chatgpt'],
                         'description': 'Sample addon description for full text search',
                         'description_language': None,
                         'description_language_confidence': None,
                         'description_html': '<p>Sample addon <b>description</b> for full text search</p>',
                         'description_pre_wrap': True,
                         'other_items_count': 2,
                         'package_size_kb': 230,
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
                       'fork_count': None,
                       'open_issues': None,
                       'size_kb': None,
                       'topics': [],
                       'repo_description': None,
                       'homepage': None,
                       'archived': None,
                       'pushed_at': None,
                       'created_at': None,
                       'primary_language': None,
                       'language_bytes': [{'name': 'Python', 'bytes': 5}, {'name': 'Rust', 'bytes': 2}],
                       'manifest': None, 'manifest_path': None,
                       'dependencies': [],
                       'readme': None,
                       'ai_tooling_markers': ['claude-code', 'cursor'], 'repo_source': None,
                                    'fork_source': None,
                                    'shared_with': [], 'repo_sharing': None,
                                    'release_count': 2,
                                    'latest_release_tag': 'v1.0',
                                    'latest_release_at': '2023-03-01T08:00:00',
                                    'release_downloads': 12,
                                    'releases': [
                                        {'tag_name': 'v1.1-beta', 'name': None,
                                         'published_at': '2023-03-10T09:00:00', 'prerelease': True,
                                         'assets': numpy.array([{'name': 'note_size.ankiaddon', 'size': 2048,
                                                                 'download_count': 3}])},
                                        {'tag_name': 'v1.0', 'name': 'First release',
                                         'published_at': '2023-03-01T08:00:00', 'prerelease': False,
                                         'assets': numpy.array([{'name': 'note_size.ankiaddon', 'size': 1024,
                                                                 'download_count': 9}])}],
                                    'contributor_count': 2,
                                    'contributors': [{'login': 'John', 'contributions': 40},
                                                     {'login': 'Jane', 'contributions': 2}],
                                    'commits_last_year': 4,
                                    'weekly_commits': [0] * 50 + [3, 1],
                                    'has_issues_enabled': True,
                                    'open_issue_count': 2,
                                    'closed_issue_count': 5,
                                    'open_pr_count': 1,
                                    'closed_pr_count': 1,
                                    'merged_pr_count': 3,
                                    'last_issue_closed_at': '2023-03-14T10:00:00',
                                    'median_first_response_hours': 6.5,
                                    'first_response_sample': 4,
                                    'outside_pr_merge_share': 0.5,
                                    'outside_prs_merged': 1,
                                    'outside_prs_decided': 2},
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
                         'forks': [],
                         'package': None
        }]
    )
    pdt.assert_frame_equal(act_df, exp_df)


def test_export_tags(snapshot_dir: SnapshotDir, dataset_snapshot_metadata: DatasetSnapshotMetadata,
                     raw_metadata: RawMetadata):
    tags: list[AiTagDefinition] = [AiTagDefinition(AiTag("statistics"), AiTagGroup("function"), "Graphs"),
                                   AiTagDefinition(AiTag("paid"), AiTagGroup("status"), "Patreon-only")]
    final_dir: Path = snapshot_dir.get_final_dir()
    exporter: ParquetExporter = ParquetExporter(final_dir)
    exporter.export_tags(tags, dataset_snapshot_metadata, raw_metadata)

    act_file: Path = final_dir / "parquet" / "tags.parquet"
    act_df: DataFrame = pandas.read_parquet(act_file)
    exp_df: DataFrame = DataFrame(
        [{'name': 'statistics', 'group': 'function', 'description': 'Graphs'},
         {'name': 'paid', 'group': 'status', 'description': 'Patreon-only'}]
    )
    pdt.assert_frame_equal(act_df, exp_df)


def test_export_anki_versions(snapshot_dir: SnapshotDir, dataset_snapshot_metadata: DatasetSnapshotMetadata,
                              raw_metadata: RawMetadata):
    anki_versions: list[AnkiRelease] = [
        AnkiRelease(AnkiVersion("25.09.2"), AnkiPointVersion(250902), date(2025, 10, 1)),
        AnkiRelease(AnkiVersion("2.1.66"), AnkiPointVersion(66))]
    final_dir: Path = snapshot_dir.get_final_dir()
    exporter: ParquetExporter = ParquetExporter(final_dir)
    exporter.export_anki_versions(anki_versions, dataset_snapshot_metadata, raw_metadata)

    act_file: Path = final_dir / "parquet" / "anki_versions.parquet"
    act_df: DataFrame = pandas.read_parquet(act_file)
    exp_df: DataFrame = DataFrame([{'version': '25.09.2', 'point_version': 250902, 'release_date': date(2025, 10, 1)},
                                   {'version': '2.1.66', 'point_version': 66, 'release_date': None}])
    pdt.assert_frame_equal(act_df, exp_df)


def test_export_anki_versions_without_dates_keeps_date_type(
        snapshot_dir: SnapshotDir, dataset_snapshot_metadata: DatasetSnapshotMetadata, raw_metadata: RawMetadata):
    final_dir: Path = snapshot_dir.get_final_dir()
    exporter: ParquetExporter = ParquetExporter(final_dir)
    exporter.export_anki_versions([AnkiRelease(AnkiVersion("2.1.66"), AnkiPointVersion(66))],
                                  dataset_snapshot_metadata, raw_metadata)

    schema: pyarrow.Schema = pyarrow.parquet.read_schema(final_dir / "parquet" / "anki_versions.parquet")
    assert schema.field("release_date").type == pyarrow.date32()


def test_export_anki_versions_empty(snapshot_dir: SnapshotDir, dataset_snapshot_metadata: DatasetSnapshotMetadata,
                                    raw_metadata: RawMetadata):
    final_dir: Path = snapshot_dir.get_final_dir()
    exporter: ParquetExporter = ParquetExporter(final_dir)
    exporter.export_anki_versions([], dataset_snapshot_metadata, raw_metadata)

    act_df: DataFrame = pandas.read_parquet(final_dir / "parquet" / "anki_versions.parquet")
    assert list(act_df.columns) == ['version', 'point_version', 'release_date']
    assert str(act_df['point_version'].dtype) == 'int64'
    assert act_df.empty
    schema: pyarrow.Schema = pyarrow.parquet.read_schema(final_dir / "parquet" / "anki_versions.parquet")
    assert schema.field("release_date").type == pyarrow.date32()


def test_export_reviews(snapshot_dir: SnapshotDir):
    reviews: list[ReviewRow] = [
        ReviewRow(AddonId(1188705668), AddonReview(ReviewVote.DISLIKE, date(2026, 7, 5), "Produces errors", None)),
        ReviewRow(AddonId(1188705668), AddonReview(ReviewVote.LIKE, date(2025, 6, 6), "Works\nfine", "Thank you!"))]
    final_dir: Path = snapshot_dir.get_final_dir()
    exporter: ParquetExporter = ParquetExporter(final_dir)
    exporter.export_reviews(reviews)

    act_df: DataFrame = pandas.read_parquet(final_dir / "parquet" / "reviews.parquet")
    exp_df: DataFrame = DataFrame([
        {'addon_id': 1188705668, 'date': date(2026, 7, 5), 'vote': 'dislike', 'text': 'Produces errors',
         'author_reply': None},
        {'addon_id': 1188705668, 'date': date(2025, 6, 6), 'vote': 'like', 'text': 'Works\nfine',
         'author_reply': 'Thank you!'}])
    pdt.assert_frame_equal(act_df, exp_df)


def test_export_reviews_empty(snapshot_dir: SnapshotDir):
    final_dir: Path = snapshot_dir.get_final_dir()
    exporter: ParquetExporter = ParquetExporter(final_dir)
    exporter.export_reviews([])

    act_df: DataFrame = pandas.read_parquet(final_dir / "parquet" / "reviews.parquet")
    assert list(act_df.columns) == ['addon_id', 'date', 'vote', 'text', 'author_reply']
    assert act_df.empty


def test_export_packages(snapshot_dir: SnapshotDir):
    packages: list[PackageRow] = [
        PackageRow(AddonId(100), AddonPackage(
            "45-2026-01-15-0123456789ab.ankiaddon", AnkiPointVersion(45), date(2026, 1, 15), 10, '{"name": "A"}', None,
            2, 30, 1, 4, ["__init__.py", "manifest.json"], {LanguageName("Python"): 25, LanguageName("JSON"): 5}))]
    final_dir: Path = snapshot_dir.get_final_dir()
    ParquetExporter(final_dir).export_packages(packages)

    act_rows: list[dict] = pyarrow.parquet.read_table(final_dir / "parquet" / "packages.parquet").to_pylist()
    assert act_rows == [{'addon_id': 100, 'file_name': '45-2026-01-15-0123456789ab.ankiaddon',
                         'min_point_version': 45, 'updated': date(2026, 1, 15), 'size_bytes': 10,
                         'manifest_json': '{"name": "A"}', 'config_json': None, 'file_count': 2,
                         'uncompressed_bytes': 30, 'python_file_count': 1, 'python_lines': 4,
                         'files': ['__init__.py', 'manifest.json'],
                         'language_bytes': [{'name': 'Python', 'bytes': 25}, {'name': 'JSON', 'bytes': 5}]}]


def test_export_packages_empty_keeps_types(snapshot_dir: SnapshotDir):
    final_dir: Path = snapshot_dir.get_final_dir()
    ParquetExporter(final_dir).export_packages([])

    schema: pyarrow.Schema = pyarrow.parquet.read_schema(final_dir / "parquet" / "packages.parquet")
    assert schema.names == ['addon_id', 'file_name', 'min_point_version', 'updated', 'size_bytes', 'manifest_json',
                            'config_json', 'file_count', 'uncompressed_bytes', 'python_file_count', 'python_lines',
                            'files', 'language_bytes']
    assert schema.field("updated").type == pyarrow.date32()
    assert schema.field("files").type == pyarrow.list_(pyarrow.string())
    assert pyarrow.parquet.read_table(final_dir / "parquet" / "packages.parquet").num_rows == 0
