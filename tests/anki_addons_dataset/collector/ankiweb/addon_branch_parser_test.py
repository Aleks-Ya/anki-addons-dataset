import datetime

from anki_addons_dataset.collector.ankiweb.addon_branch_parser import AddonBranchParser
from anki_addons_dataset.common.data_types import AddonBranch, AnkiVersion


def test_extract_addon_branch():
    assert AddonBranchParser.extract_addon_branch("24.04.1-25.02.1+ (Updated 2025-04-19)") == AddonBranch(
        min_anki_version=AnkiVersion('24.04.1'),
        max_anki_version=AnkiVersion('25.02.1+'),
        updated=datetime.date(2025, 4, 19))

    assert AddonBranchParser.extract_addon_branch("23.10-25.02.5 (Updated 2024-05-16)") == AddonBranch(
        min_anki_version=AnkiVersion('23.10'),
        max_anki_version=AnkiVersion('25.02.5'),
        updated=datetime.date(2024, 5, 16))

    assert AddonBranchParser.extract_addon_branch("2.1.1+ (Updated 2025-02-25)") == AddonBranch(
        min_anki_version=AnkiVersion('2.1.1'),
        max_anki_version=AnkiVersion('+'),
        updated=datetime.date(2025, 2, 25))

    assert AddonBranchParser.extract_addon_branch("2.1.0 (Updated 2023-06-27)") == AddonBranch(
        min_anki_version=AnkiVersion('2.1.0'),
        max_anki_version=None,
        updated=datetime.date(2023, 6, 27))
