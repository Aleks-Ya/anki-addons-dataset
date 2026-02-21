import datetime

from anki_addons_dataset.collector.ankiweb.version_parser import VersionParser
from anki_addons_dataset.common.data_types import Version


def test_extract_version():
    assert VersionParser.extract_version("24.04.1-25.02.1+ (Updated 2025-04-19)") == Version(
        min_version='24.04.1', max_version='25.02.1+', updated=datetime.date(2025, 4, 19))
    assert VersionParser.extract_version("2.1.1+ (Updated 2025-02-25)") == Version(
        min_version='2.1.1', max_version='+', updated=datetime.date(2025, 2, 25))
