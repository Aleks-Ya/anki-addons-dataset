from pathlib import Path
from typing import Optional

import pandas
from pandas import DataFrame
import pandas.testing as pdt

from anki_addons_dataset.common.data_types import Aggregation, AddonInfos, AddonInfo, AnkiForumInfo, \
    DatasetVersionMetadata, RawMetadata
from anki_addons_dataset.common.working_dir import VersionDir
from anki_addons_dataset.exporter.xlsx.xlsx_exporter import XlsxExporter


def test_export_addon_infos(xlsx_exporter: XlsxExporter, version_dir: VersionDir, addon_infos: AddonInfos,
                            dataset_version_metadata: DatasetVersionMetadata, raw_metadata: RawMetadata):
    xlsx_exporter.export_addon_infos(addon_infos, dataset_version_metadata, raw_metadata)
    act_file: Path = version_dir.get_final_dir() / "xlsx" / "data.xlsx"
    act_df: DataFrame = pandas.read_excel(act_file)
    exp_file: Path = Path(__file__).parent / "exp_data.xlsx"
    exp_df: DataFrame = pandas.read_excel(exp_file)
    pdt.assert_frame_equal(act_df, exp_df)


def test_export_addon_infos_empty_forum(xlsx_exporter: XlsxExporter, version_dir: VersionDir, addon_info: AddonInfo,
                                        dataset_version_metadata: DatasetVersionMetadata, raw_metadata: RawMetadata):
    forum: Optional[AnkiForumInfo] = None
    addon_info.forum = forum
    addon_infos: AddonInfos = AddonInfos([addon_info])

    xlsx_exporter.export_addon_infos(addon_infos, dataset_version_metadata, raw_metadata)
    act_file: Path = version_dir.get_final_dir() / "xlsx" / "data.xlsx"
    act_df: DataFrame = pandas.read_excel(act_file)
    exp_file: Path = Path(__file__).parent / "exp_data_empty_forum.xlsx"
    exp_df: DataFrame = pandas.read_excel(exp_file)
    pdt.assert_frame_equal(act_df, exp_df)


def test_export_aggregation(xlsx_exporter: XlsxExporter, version_dir: VersionDir,
                            dataset_version_metadata: DatasetVersionMetadata, raw_metadata: RawMetadata):
    aggregation: Aggregation = Aggregation(addon_number=5,
                                           addon_with_github_number=4,
                                           addon_with_anki_forum_page_number=3,
                                           addon_with_unit_tests_number=2)
    xlsx_exporter.export_aggregation(aggregation, dataset_version_metadata, raw_metadata)
    act_file: Path = version_dir.get_final_dir() / "xlsx" / "aggregation.xlsx"
    act_df: DataFrame = pandas.read_excel(act_file)
    exp_file: Path = Path(__file__).parent / "exp_aggregation.xlsx"
    exp_df: DataFrame = pandas.read_excel(exp_file)
    pdt.assert_frame_equal(act_df, exp_df)
