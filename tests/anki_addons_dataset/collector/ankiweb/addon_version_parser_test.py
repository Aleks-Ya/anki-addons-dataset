import datetime

from anki_addons_dataset.collector.ankiweb.addon_version_parser import AddonVersionParser
from anki_addons_dataset.common.data_types import AddonVersion


def test_extract_version():
    assert AddonVersionParser.extract_addon_version("24.04.1-25.02.1+ (Updated 2025-04-19)") == AddonVersion(
        min_version='24.04.1', max_version='25.02.1+', updated=datetime.date(2025, 4, 19))

    assert AddonVersionParser.extract_addon_version("23.10-25.02.5 (Updated 2024-05-16)") == AddonVersion(
        min_version='23.10', max_version='25.02.5', updated=datetime.date(2024, 5, 16))

    assert AddonVersionParser.extract_addon_version("2.1.1+ (Updated 2025-02-25)") == AddonVersion(
        min_version='2.1.1', max_version='+', updated=datetime.date(2025, 2, 25))

    assert AddonVersionParser.extract_addon_version("2.1.0 (Updated 2023-06-27)") == AddonVersion(
        min_version='2.1.0', max_version=None, updated=datetime.date(2023, 6, 27))
