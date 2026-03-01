from pathlib import Path

import pandas
from pandas import DataFrame
import pandas.testing as pdt

from anki_addons_dataset.common.data_types import Aggregation, AddonInfos
from anki_addons_dataset.common.working_dir import VersionDir
from anki_addons_dataset.exporter.xlsx.xlsx_exporter import XlsxExporter


def test_export_addon_infos(version_dir: VersionDir, addon_infos: AddonInfos):
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
