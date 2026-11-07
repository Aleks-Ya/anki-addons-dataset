import dataclasses
from datetime import date
from pathlib import Path
from typing import Optional
from unittest.mock import Mock
from zipfile import ZipFile

import pytest

from anki_addons_dataset.collector.package.package_analyzer import PackageAnalyzer
from anki_addons_dataset.collector.package.package_enricher import PackageEnricher
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AddonPackage, AddonPackages, \
    AnkiPointVersion, LanguageName
from anki_addons_dataset.common.working_dir import SnapshotDir

__ADDON_ID: AddonId = AddonId(100)


def __add_package(snapshot_dir: SnapshotDir, file_name: str, content: bytes = b"a = 1\n",
                  addon_id: AddonId = __ADDON_ID) -> Path:
    package_file: Path = snapshot_dir.get_package_dir() / str(addon_id) / file_name
    package_file.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(package_file, "w") as archive:
        archive.writestr("__init__.py", content)
    return package_file


def __enrich(snapshot_dir: SnapshotDir, addon_info: AddonInfo) -> Optional[AddonPackages]:
    header = dataclasses.replace(addon_info.header, id=__ADDON_ID)
    addon_infos: AddonInfos = AddonInfos([dataclasses.replace(addon_info, header=header)])
    return PackageEnricher(snapshot_dir, PackageAnalyzer()).enrich(addon_infos)[0].package


def test_enrich_builds_a_package_from_the_file(snapshot_dir: SnapshotDir, addon_info: AddonInfo):
    package_file: Path = __add_package(snapshot_dir, "45-2026-01-15-0123456789ab.ankiaddon")

    packages: Optional[AddonPackages] = __enrich(snapshot_dir, addon_info)

    assert packages == AddonPackages([AddonPackage(
        "45-2026-01-15-0123456789ab.ankiaddon", AnkiPointVersion(45), date(2026, 1, 15), package_file.stat().st_size,
        None, None, 1, 6, 1, 1, ["__init__.py"], {})])


def test_enrich_passes_the_detected_languages(snapshot_dir: SnapshotDir, addon_info: AddonInfo):
    __add_package(snapshot_dir, "45-2026-01-15-0123456789ab.ankiaddon", b"import aqt\nprint(1)")

    packages: Optional[AddonPackages] = __enrich(snapshot_dir, addon_info)

    assert packages.branches[0].language_bytes == {LanguageName("Python"): 19}


def test_enrich_sorts_branches_by_point_version(snapshot_dir: SnapshotDir, addon_info: AddonInfo):
    __add_package(snapshot_dir, "231000-2026-01-15-0123456789ab.ankiaddon")
    __add_package(snapshot_dir, "45-2025-01-15-0123456789ab.ankiaddon")

    packages: Optional[AddonPackages] = __enrich(snapshot_dir, addon_info)

    assert [branch.min_point_version for branch in packages.branches] == [45, 231000]


def test_enrich_keeps_the_newest_file_of_a_branch(snapshot_dir: SnapshotDir, addon_info: AddonInfo):
    __add_package(snapshot_dir, "45-2026-01-15-aaaaaaaaaaaa.ankiaddon")
    __add_package(snapshot_dir, "45-2026-02-15-bbbbbbbbbbbb.ankiaddon")
    __add_package(snapshot_dir, "45-2025-12-15-cccccccccccc.ankiaddon")

    packages: Optional[AddonPackages] = __enrich(snapshot_dir, addon_info)

    assert [branch.file_name for branch in packages.branches] == ["45-2026-02-15-bbbbbbbbbbbb.ankiaddon"]


def test_enrich_leaves_an_addon_without_packages_empty(snapshot_dir: SnapshotDir, addon_info: AddonInfo):
    assert __enrich(snapshot_dir, addon_info) is None


def test_enrich_does_not_read_packages_of_other_addons(snapshot_dir: SnapshotDir, addon_info: AddonInfo):
    __add_package(snapshot_dir, "45-2026-01-15-0123456789ab.ankiaddon", addon_id=AddonId(200))

    assert __enrich(snapshot_dir, addon_info) is None


def test_enrich_ignores_unexpected_file_names(snapshot_dir: SnapshotDir, addon_info: AddonInfo):
    __add_package(snapshot_dir, "45-2026-01-15-part.ankiaddon")

    assert __enrich(snapshot_dir, addon_info) is None


def test_enrich_skips_a_corrupt_package_with_a_warning(snapshot_dir: SnapshotDir, addon_info: AddonInfo,
                                                       caplog: pytest.LogCaptureFixture):
    __add_package(snapshot_dir, "45-2026-01-15-0123456789ab.ankiaddon")
    corrupt: Path = __add_package(snapshot_dir, "231000-2026-01-15-0123456789ab.ankiaddon")
    corrupt.write_bytes(b"not a zip")

    packages: Optional[AddonPackages] = __enrich(snapshot_dir, addon_info)

    assert [branch.min_point_version for branch in packages.branches] == [45]
    assert "1 packages cannot be read" in caplog.text


def test_enrich_keeps_other_fields(snapshot_dir: SnapshotDir, addon_info: AddonInfo):
    __add_package(snapshot_dir, "45-2026-01-15-0123456789ab.ankiaddon", addon_id=addon_info.header.id)

    enriched: AddonInfo = PackageEnricher(snapshot_dir, PackageAnalyzer()).enrich(AddonInfos([addon_info]))[0]

    assert dataclasses.replace(enriched, package=None) == addon_info


def test_enrich_does_not_hide_a_programming_error(snapshot_dir: SnapshotDir, addon_info: AddonInfo):
    __add_package(snapshot_dir, "45-2026-01-15-0123456789ab.ankiaddon")
    package_analyzer: Mock = Mock(spec=PackageAnalyzer)
    package_analyzer.analyze.side_effect = TypeError("bug")
    addon_infos: AddonInfos = AddonInfos([dataclasses.replace(
        addon_info, header=dataclasses.replace(addon_info.header, id=__ADDON_ID))])
    package_enricher: PackageEnricher = PackageEnricher(snapshot_dir, package_analyzer)

    with pytest.raises(TypeError, match="bug"):
        package_enricher.enrich(addon_infos)
