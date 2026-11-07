import dataclasses
import hashlib
import io
import json
import logging
from datetime import date
from pathlib import Path
from typing import Optional
from unittest.mock import Mock
from zipfile import ZipFile, ZipInfo

import pytest
from requests import ConnectionError as RequestsConnectionError

from anki_addons_dataset.collector.package.package_cache_index import PackageCacheIndex
from anki_addons_dataset.collector.package.package_client import PackageClient, PackageError, PackageLocation
from anki_addons_dataset.collector.package.package_collector import PackageCollector
from anki_addons_dataset.common.data_types import AddonBranch, AddonId, AddonInfo, AddonInfos, AnkiPointVersion, \
    AnkiVersion, SnapshotDate
from anki_addons_dataset.common.working_dir import SnapshotDir, WorkingDir

__ADDON_ID: AddonId = AddonId(100)
__UPDATED: date = date(2026, 1, 15)


def __zip_bytes(content: str = "code") -> bytes:
    buffer: io.BytesIO = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(ZipInfo("__init__.py", date_time=(2026, 1, 15, 0, 0, 0)), content)
    return buffer.getvalue()


def __branch(min_point: Optional[int] = 45, max_point: Optional[int] = 50, updated: date = __UPDATED) -> AddonBranch:
    return AddonBranch(AnkiVersion("min"), AnkiVersion("max"), updated, min_point, max_point)


def __addon_infos(addon_info: AddonInfo, branches: list[AddonBranch]) -> AddonInfos:
    header = dataclasses.replace(addon_info.header, id=__ADDON_ID, anki_point_version=AnkiPointVersion(250900))
    page = dataclasses.replace(addon_info.page, branches=branches)
    return AddonInfos([dataclasses.replace(addon_info, header=header, page=page)])


def __location(min_point: int = 45, uploaded: date = __UPDATED) -> PackageLocation:
    return PackageLocation(f"/svc/{min_point}", AnkiPointVersion(min_point), uploaded)


def __client(content: Optional[bytes] = None, location: Optional[PackageLocation] = None) -> Mock:
    def download(_: PackageLocation, part_file: Path) -> bool:
        part_file.write_bytes(content if content is not None else __zip_bytes())
        return True

    client: Mock = Mock(spec=PackageClient)
    client.locate.return_value = location if location is not None else __location()
    client.download.side_effect = download
    return client


def __snapshot(working_dir: WorkingDir, day: str) -> SnapshotDir:
    return working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat(day))).create()


def __collect(working_dir: WorkingDir, snapshot_dir: SnapshotDir, client: Mock, addon_infos: AddonInfos) -> None:
    index: PackageCacheIndex = PackageCacheIndex.load(working_dir.list_snapshot_dirs())
    PackageCollector(snapshot_dir, client, index).collect(addon_infos)


def __files(snapshot_dir: SnapshotDir) -> list[Path]:
    return sorted((snapshot_dir.get_package_dir() / str(__ADDON_ID)).iterdir())


def __exp_name(content: bytes, min_point: int = 45, updated: date = __UPDATED) -> str:
    return f"{min_point}-{updated.isoformat()}-{hashlib.sha256(content).hexdigest()[:12]}.ankiaddon"


def test_downloads_missing_package(working_dir: WorkingDir, addon_info: AddonInfo):
    snapshot_dir: SnapshotDir = __snapshot(working_dir, "2026-02-01")
    client: Mock = __client()

    __collect(working_dir, snapshot_dir, client, __addon_infos(addon_info, [__branch()]))

    client.locate.assert_called_once_with(__ADDON_ID, 45)
    assert [file.name for file in __files(snapshot_dir)] == [__exp_name(__zip_bytes())]


def test_logs_downloaded_package(working_dir: WorkingDir, addon_info: AddonInfo, caplog: pytest.LogCaptureFixture):
    snapshot_dir: SnapshotDir = __snapshot(working_dir, "2026-02-01")

    with caplog.at_level(logging.INFO):
        __collect(working_dir, snapshot_dir, __client(), __addon_infos(addon_info, [__branch()]))

    assert f"Downloaded package of addon {__ADDON_ID}: {__exp_name(__zip_bytes())}" in caplog.messages


def test_writes_package_list(working_dir: WorkingDir, addon_info: AddonInfo):
    snapshot_dir: SnapshotDir = __snapshot(working_dir, "2026-02-01")

    __collect(working_dir, snapshot_dir, __client(), __addon_infos(addon_info, [__branch()]))

    assert json.loads(snapshot_dir.get_package_list_file().read_text()) == [f"{__ADDON_ID}/{__exp_name(__zip_bytes())}"]


def test_resume_makes_no_request(working_dir: WorkingDir, addon_info: AddonInfo):
    snapshot_dir: SnapshotDir = __snapshot(working_dir, "2026-02-01")
    addon_infos: AddonInfos = __addon_infos(addon_info, [__branch()])
    __collect(working_dir, snapshot_dir, __client(), addon_infos)
    client: Mock = __client()

    __collect(working_dir, snapshot_dir, client, addon_infos)

    client.locate.assert_not_called()
    client.download.assert_not_called()


def test_older_snapshot_hit_makes_no_request_and_shares_inode(working_dir: WorkingDir, addon_info: AddonInfo):
    old_snapshot: SnapshotDir = __snapshot(working_dir, "2026-02-01")
    new_snapshot: SnapshotDir = __snapshot(working_dir, "2026-03-01")
    addon_infos: AddonInfos = __addon_infos(addon_info, [__branch()])
    __collect(working_dir, old_snapshot, __client(), addon_infos)
    client: Mock = __client()

    __collect(working_dir, new_snapshot, client, addon_infos)

    client.locate.assert_not_called()
    assert __files(new_snapshot)[0].stat().st_ino == __files(old_snapshot)[0].stat().st_ino


def test_branch_updated_on_holding_snapshot_day_is_downloaded_again(working_dir: WorkingDir, addon_info: AddonInfo):
    old_snapshot: SnapshotDir = __snapshot(working_dir, "2026-01-15")
    new_snapshot: SnapshotDir = __snapshot(working_dir, "2026-03-01")
    addon_infos: AddonInfos = __addon_infos(addon_info, [__branch()])
    __collect(working_dir, old_snapshot, __client(__zip_bytes("first")), addon_infos)
    client: Mock = __client(__zip_bytes("second"))

    __collect(working_dir, new_snapshot, client, addon_infos)

    client.download.assert_called_once()
    assert [file.name for file in __files(new_snapshot)] == [__exp_name(__zip_bytes("second"))]
    assert [file.name for file in __files(old_snapshot)] == [__exp_name(__zip_bytes("first"))]


def test_identical_redownload_shares_inode(working_dir: WorkingDir, addon_info: AddonInfo):
    old_snapshot: SnapshotDir = __snapshot(working_dir, "2026-01-15")
    new_snapshot: SnapshotDir = __snapshot(working_dir, "2026-03-01")
    addon_infos: AddonInfos = __addon_infos(addon_info, [__branch()])
    __collect(working_dir, old_snapshot, __client(), addon_infos)
    client: Mock = __client()

    __collect(working_dir, new_snapshot, client, addon_infos)

    client.download.assert_called_once()
    assert __files(new_snapshot)[0].stat().st_ino == __files(old_snapshot)[0].stat().st_ino


def test_overlapping_branch_falls_back_to_max_point_version(working_dir: WorkingDir, addon_info: AddonInfo):
    snapshot_dir: SnapshotDir = __snapshot(working_dir, "2026-02-01")
    client: Mock = __client()
    client.locate.side_effect = [__location(24), __location(36)]

    __collect(working_dir, snapshot_dir, client, __addon_infos(addon_info, [__branch(36, 38)]))

    assert [call.args[1] for call in client.locate.call_args_list] == [36, 38]
    assert [file.name for file in __files(snapshot_dir)] == [__exp_name(__zip_bytes(), 36)]


def test_branch_never_matched_keeps_no_file(working_dir: WorkingDir, addon_info: AddonInfo):
    snapshot_dir: SnapshotDir = __snapshot(working_dir, "2026-02-01")
    client: Mock = __client(location=__location(24))

    __collect(working_dir, snapshot_dir, client, __addon_infos(addon_info, [__branch(36, 38)]))

    client.download.assert_not_called()
    assert not (snapshot_dir.get_package_dir() / str(__ADDON_ID)).exists()


def test_addon_without_branches_uses_redirect_values(working_dir: WorkingDir, addon_info: AddonInfo):
    snapshot_dir: SnapshotDir = __snapshot(working_dir, "2026-02-01")
    client: Mock = __client(location=__location(0))

    __collect(working_dir, snapshot_dir, client, __addon_infos(addon_info, []))

    client.locate.assert_called_once_with(__ADDON_ID, 250900)
    assert [file.name for file in __files(snapshot_dir)] == [__exp_name(__zip_bytes(), 0)]


def test_addon_without_branches_falls_back_to_point_version_zero(working_dir: WorkingDir, addon_info: AddonInfo):
    snapshot_dir: SnapshotDir = __snapshot(working_dir, "2026-02-01")
    client: Mock = __client()
    client.locate.side_effect = [None, __location(0)]

    __collect(working_dir, snapshot_dir, client, __addon_infos(addon_info, []))

    assert [call.args[1] for call in client.locate.call_args_list] == [250900, 0]
    assert len(__files(snapshot_dir)) == 1


def test_addon_without_branches_skips_body_on_hit(working_dir: WorkingDir, addon_info: AddonInfo):
    old_snapshot: SnapshotDir = __snapshot(working_dir, "2026-02-01")
    new_snapshot: SnapshotDir = __snapshot(working_dir, "2026-03-01")
    addon_infos: AddonInfos = __addon_infos(addon_info, [])
    __collect(working_dir, old_snapshot, __client(location=__location(0)), addon_infos)
    client: Mock = __client(location=__location(0))

    __collect(working_dir, new_snapshot, client, addon_infos)

    client.locate.assert_called_once()
    client.download.assert_not_called()
    assert len(__files(new_snapshot)) == 1


@pytest.mark.parametrize("branches", [[__branch()], []])
def test_location_404_does_not_stop_the_run(working_dir: WorkingDir, addon_info: AddonInfo,
                                            branches: list[AddonBranch]):
    snapshot_dir: SnapshotDir = __snapshot(working_dir, "2026-02-01")
    client: Mock = __client()
    client.locate.return_value = None

    __collect(working_dir, snapshot_dir, client, __addon_infos(addon_info, branches))

    assert json.loads(snapshot_dir.get_package_list_file().read_text()) == []


def test_body_404_leaves_no_file(working_dir: WorkingDir, addon_info: AddonInfo, caplog: pytest.LogCaptureFixture):
    snapshot_dir: SnapshotDir = __snapshot(working_dir, "2026-02-01")
    client: Mock = __client()
    client.download.side_effect = None
    client.download.return_value = False

    with caplog.at_level(logging.INFO):
        __collect(working_dir, snapshot_dir, client, __addon_infos(addon_info, [__branch()]))

    assert __files(snapshot_dir) == []
    assert not any(message.startswith("Downloaded package") for message in caplog.messages)


def test_invalid_zip_is_removed(working_dir: WorkingDir, addon_info: AddonInfo):
    snapshot_dir: SnapshotDir = __snapshot(working_dir, "2026-02-01")

    __collect(working_dir, snapshot_dir, __client(b"not a zip"), __addon_infos(addon_info, [__branch()]))

    assert __files(snapshot_dir) == []


def test_failed_download_removes_part_file_and_continues_with_next_branch(working_dir: WorkingDir,
                                                                          addon_info: AddonInfo):
    snapshot_dir: SnapshotDir = __snapshot(working_dir, "2026-02-01")
    client: Mock = __client()
    client.locate.side_effect = [__location(45), __location(60)]

    def download(location: PackageLocation, part_file: Path) -> bool:
        part_file.write_bytes(__zip_bytes())
        if location.min_point_version == 45:
            raise PackageError("broken")
        return True

    client.download.side_effect = download

    __collect(working_dir, snapshot_dir, client, __addon_infos(addon_info, [__branch(45, 50), __branch(60, 70)]))

    assert [file.name for file in __files(snapshot_dir)] == [__exp_name(__zip_bytes(), 60)]


def test_a_request_failure_is_counted_as_a_failed_package(working_dir: WorkingDir, addon_info: AddonInfo,
                                                          caplog: pytest.LogCaptureFixture):
    snapshot_dir: SnapshotDir = __snapshot(working_dir, "2026-02-01")
    client: Mock = __client()
    client.locate.side_effect = RequestsConnectionError("reset")

    __collect(working_dir, snapshot_dir, client, __addon_infos(addon_info, [__branch()]))

    assert "failed: 1" in caplog.text


def test_a_programming_error_is_not_counted_as_a_failed_package(working_dir: WorkingDir, addon_info: AddonInfo):
    snapshot_dir: SnapshotDir = __snapshot(working_dir, "2026-02-01")
    client: Mock = __client()
    client.locate.side_effect = TypeError("bug")
    addon_infos: AddonInfos = __addon_infos(addon_info, [__branch()])

    with pytest.raises(TypeError, match="bug"):
        __collect(working_dir, snapshot_dir, client, addon_infos)
