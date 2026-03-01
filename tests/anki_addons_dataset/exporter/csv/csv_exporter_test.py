from pathlib import Path
from textwrap import dedent

from anki_addons_dataset.common.data_types import AddonId, Aggregation, AddonInfos
from anki_addons_dataset.common.working_dir import VersionDir
from anki_addons_dataset.exporter.csv.csv_exporter import CsvExporter


def test_export_addon_infos(version_dir: VersionDir, addon_infos: AddonInfos):
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
