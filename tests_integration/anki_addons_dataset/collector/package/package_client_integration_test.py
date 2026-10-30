import zipfile
from pathlib import Path
from typing import Optional

from anki_addons_dataset.collector.package.package_client import PackageClient, PackageLocation
from anki_addons_dataset.common.data_types import AddonId, AnkiPointVersion


def test_locate_and_download_package(known_addon_id: AddonId, tmp_path: Path):
    client: PackageClient = PackageClient()
    point_version: AnkiPointVersion = AnkiPointVersion(250900)

    location: Optional[PackageLocation] = client.locate(known_addon_id, point_version)

    assert location is not None
    assert location.min_point_version <= point_version
    part_file: Path = tmp_path / "package.part"
    assert client.download(location, part_file)
    assert zipfile.is_zipfile(part_file)


def test_locate_returns_none_for_unknown_addon():
    assert PackageClient().locate(AddonId(999999999), AnkiPointVersion(250900)) is None
