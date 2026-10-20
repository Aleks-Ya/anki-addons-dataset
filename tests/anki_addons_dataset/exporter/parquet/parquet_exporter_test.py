from pathlib import Path

import pandas
from pandas import DataFrame
import pandas.testing as pdt

from anki_addons_dataset.common.data_types import Aggregation, AddonInfos, DatasetSnapshotMetadata, RawMetadata, \
    AiTagDefinition, AiTag, AiTagGroup
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
                      'posts_count': 42},
            'ai': {'summary': 'Shows the size of the collection and of individual notes.',
                   'model': 'test-model',
                   'tags': ['statistics']},
            'author': {'id': 1188705668, 'addon_count': 3},
                         'forked_from': [],
                         'forks': []
        }]
    )
    pdt.assert_frame_equal(act_df, exp_df)


def test_export_aggregation(snapshot_dir: SnapshotDir, dataset_snapshot_metadata: DatasetSnapshotMetadata,
                            raw_metadata: RawMetadata):
    aggregation: Aggregation = Aggregation(addon_number=5,
                                           addon_with_github_number=4,
                                           addon_with_anki_forum_page_number=3,
                                           addon_with_unit_tests_number=2,
                                           author_number=1)
    final_dir: Path = snapshot_dir.get_final_dir()
    exporter: ParquetExporter = ParquetExporter(final_dir)
    exporter.export_aggregation(aggregation, dataset_snapshot_metadata, raw_metadata)

    act_file: Path = final_dir / "parquet" / "aggregation.parquet"
    act_df: DataFrame = pandas.read_parquet(act_file)
    exp_df: DataFrame = DataFrame(
        [{'addon_number': 5,
          'addon_with_github_number': 4,
          'addon_with_anki_forum_page_number': 3,
          'addon_with_unit_tests_number': 2,
          'author_number': 1}]
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
