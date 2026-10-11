import datetime

from anki_addons_dataset.collector.ankiweb.addon_branch_parser import AddonBranchParser
from anki_addons_dataset.common.data_types import AddonBranch, AnkiVersion, AnkiPointVersion, AnkiVersionKind


def test_extract_addon_branch():
    assert AddonBranchParser.extract_addon_branch("24.04.1-25.02.1+ (Updated 2025-04-19)") == AddonBranch(
        min_anki_version=AnkiVersion('24.04.1'),
        max_anki_version=AnkiVersion('25.02.1+'),
        updated=datetime.date(2025, 4, 19),
        min_point_version=AnkiPointVersion(240401),
        max_point_version=AnkiPointVersion(250201),
        max_version_kind=AnkiVersionKind.TESTED)

    assert AddonBranchParser.extract_addon_branch("23.10-25.02.5 (Updated 2024-05-16)") == AddonBranch(
        min_anki_version=AnkiVersion('23.10'),
        max_anki_version=AnkiVersion('25.02.5'),
        updated=datetime.date(2024, 5, 16),
        min_point_version=AnkiPointVersion(231000),
        max_point_version=AnkiPointVersion(250205),
        max_version_kind=AnkiVersionKind.HARD)

    assert AddonBranchParser.extract_addon_branch("2.1.1+ (Updated 2025-02-25)") == AddonBranch(
        min_anki_version=AnkiVersion('2.1.1'),
        max_anki_version=AnkiVersion('+'),
        updated=datetime.date(2025, 2, 25),
        min_point_version=AnkiPointVersion(1),
        max_point_version=None,
        max_version_kind=AnkiVersionKind.OPEN)

    assert AddonBranchParser.extract_addon_branch("2.1.0 (Updated 2023-06-27)") == AddonBranch(
        min_anki_version=AnkiVersion('2.1.0'),
        max_anki_version=None,
        updated=datetime.date(2023, 6, 27),
        min_point_version=AnkiPointVersion(0),
        max_point_version=None,
        max_version_kind=AnkiVersionKind.UNKNOWN)

    assert AddonBranchParser.extract_addon_branch("2.1.35-2.1.66+ (Updated 2023-06-27)") == AddonBranch(
        min_anki_version=AnkiVersion('2.1.35'),
        max_anki_version=AnkiVersion('2.1.66+'),
        updated=datetime.date(2023, 6, 27),
        min_point_version=AnkiPointVersion(35),
        max_point_version=AnkiPointVersion(66),
        max_version_kind=AnkiVersionKind.TESTED)
