from datetime import date
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

import pytest
from requests import ConnectionError as RequestsConnectionError, Session

from anki_addons_dataset.collector.package.package_client import PackageClient, PackageError, PackageLocation
from anki_addons_dataset.common.data_types import AddonId, AnkiPointVersion

__ADDON_ID: AddonId = AddonId(100)
__LOCATION_PATH: str = "/svc/shared/download-addon/100?t=1771706674&minpt=231000&maxpt=-250100&bidx=4"


def __response(status_code: int, location: Optional[str] = None, chunks: Optional[list[bytes]] = None) -> MagicMock:
    response: MagicMock = MagicMock()
    response.status_code = status_code
    response.headers = {"location": location} if location else {}
    response.iter_content.return_value = chunks or []
    response.__enter__.return_value = response
    return response


def __client(session: MagicMock) -> PackageClient:
    return PackageClient(lambda: session, 0)


def test_locate_reads_redirect_without_following_it():
    session: MagicMock = MagicMock(spec=Session)
    session.get.return_value = __response(303, __LOCATION_PATH)

    location: Optional[PackageLocation] = __client(session).locate(__ADDON_ID, AnkiPointVersion(231000))

    assert location == PackageLocation(__LOCATION_PATH, AnkiPointVersion(231000), date(2026, 2, 21))
    session.get.assert_called_once_with("https://ankiweb.net/shared/download/100?v=2.1&p=231000",
                                        allow_redirects=False, timeout=60)


def test_locate_returns_none_on_404():
    session: MagicMock = MagicMock(spec=Session)
    session.get.return_value = __response(404)

    assert __client(session).locate(__ADDON_ID, AnkiPointVersion(1)) is None


def test_locate_retries_transient_failures():
    session: MagicMock = MagicMock(spec=Session)
    session.get.side_effect = [RequestsConnectionError("reset"), __response(503), __response(303, __LOCATION_PATH)]

    location: Optional[PackageLocation] = __client(session).locate(__ADDON_ID, AnkiPointVersion(1))

    assert location is not None
    assert session.get.call_count == 3


def test_locate_gives_up_after_all_attempts():
    session: MagicMock = MagicMock(spec=Session)
    session.get.side_effect = RequestsConnectionError("reset")
    client: PackageClient = __client(session)
    point_version: AnkiPointVersion = AnkiPointVersion(1)

    with pytest.raises(RequestsConnectionError):
        client.locate(__ADDON_ID, point_version)

    assert session.get.call_count == 4


def test_locate_does_not_retry_a_client_error():
    session: MagicMock = MagicMock(spec=Session)
    session.get.return_value = __response(400)
    client: PackageClient = __client(session)
    point_version: AnkiPointVersion = AnkiPointVersion(-1)

    with pytest.raises(PackageError):
        client.locate(__ADDON_ID, point_version)

    session.get.assert_called_once()


def test_locate_requires_a_redirect():
    session: MagicMock = MagicMock(spec=Session)
    session.get.return_value = __response(200)
    client: PackageClient = __client(session)
    point_version: AnkiPointVersion = AnkiPointVersion(1)

    with pytest.raises(PackageError):
        client.locate(__ADDON_ID, point_version)


def test_download_streams_body_to_file(tmp_path: Path):
    session: MagicMock = MagicMock(spec=Session)
    session.get.return_value = __response(200, chunks=[b"ab", b"cd"])
    part_file: Path = tmp_path / "package.part"
    location: PackageLocation = PackageLocation(__LOCATION_PATH, AnkiPointVersion(1), date(2026, 2, 21))

    assert __client(session).download(location, part_file)

    assert part_file.read_bytes() == b"abcd"
    session.get.assert_called_once_with(f"https://ankiweb.net{__LOCATION_PATH}", stream=True, timeout=60)


def test_download_returns_false_on_404(tmp_path: Path):
    session: MagicMock = MagicMock(spec=Session)
    session.get.return_value = __response(404)
    part_file: Path = tmp_path / "package.part"
    location: PackageLocation = PackageLocation(__LOCATION_PATH, AnkiPointVersion(1), date(2026, 2, 21))

    assert not __client(session).download(location, part_file)
    assert not part_file.exists()


def test_session_is_reused_within_a_thread():
    session: MagicMock = MagicMock(spec=Session)
    session.get.return_value = __response(404)
    factory: MagicMock = MagicMock(return_value=session)
    client: PackageClient = PackageClient(factory, 0)

    client.locate(__ADDON_ID, AnkiPointVersion(1))
    client.locate(__ADDON_ID, AnkiPointVersion(2))

    factory.assert_called_once()


def test_locate_rejects_a_redirect_without_the_expected_parameters():
    session: MagicMock = MagicMock(spec=Session)
    session.get.return_value = __response(303, "/svc/shared/download-addon/100?t=soon")
    client: PackageClient = __client(session)
    point_version: AnkiPointVersion = AnkiPointVersion(1)

    with pytest.raises(PackageError, match="Unexpected download location"):
        client.locate(__ADDON_ID, point_version)
