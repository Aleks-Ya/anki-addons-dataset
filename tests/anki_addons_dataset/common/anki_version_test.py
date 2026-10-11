import logging

import pytest
from _pytest.logging import LogCaptureFixture

from anki_addons_dataset.common.anki_version import AnkiVersionCodec
from anki_addons_dataset.common.data_types import AnkiPointVersion, AnkiVersionKind


@pytest.mark.parametrize("version, point", [
    ("2.1.0", 0),
    ("2.1.66", 66),
    ("23.10", 231000),
    ("25.09.2", 250902),
    ("26.05b1", 260500),
    ("25.09rc1", 250900),
])
def test_to_point(version: str, point: int):
    assert AnkiVersionCodec.to_point(version) == point


def test_to_point_invalid():
    with pytest.raises(ValueError, match="Cannot parse Anki version: 'abc'"):
        AnkiVersionCodec.to_point("abc")


@pytest.mark.parametrize("point, version", [
    (0, "2.1.0"),
    (66, "2.1.66"),
    (231000, "23.10"),
    (250902, "25.09.2"),
])
def test_to_str(point: int, version: str):
    assert AnkiVersionCodec.to_str(AnkiPointVersion(point)) == version


def test_points_sort_chronologically():
    versions: list[str] = ["23.10", "2.1.66", "25.09.2", "2.1.9", "25.09"]
    assert sorted(versions, key=AnkiVersionCodec.to_point) == ["2.1.9", "2.1.66", "23.10", "25.09", "25.09.2"]


@pytest.mark.parametrize("header, point, kind", [
    ("25.09.2~", 250902, AnkiVersionKind.TESTED),
    ("2.1.1~", 1, AnkiVersionKind.TESTED),
    ("<=2.1.35", 35, AnkiVersionKind.HARD),
    ("<=25.09.2", 250902, AnkiVersionKind.HARD),
    ("", None, AnkiVersionKind.UNKNOWN),
])
def test_parse_header(header: str, point: int | None, kind: AnkiVersionKind):
    assert AnkiVersionCodec.parse_header(header) == (point, kind)


@pytest.mark.parametrize("header", ["abc", "25.09", "<=25.09~", "~"])
def test_parse_header_invalid(header: str, caplog: LogCaptureFixture):
    with caplog.at_level(logging.WARNING):
        assert AnkiVersionCodec.parse_header(header) == (None, AnkiVersionKind.UNKNOWN)
    assert f"Cannot parse Anki version of the addons page: {header!r}" in caplog.text


@pytest.mark.parametrize("max_point_version, point, kind", [
    (-250900, 250900, AnkiVersionKind.HARD),
    (-49, 49, AnkiVersionKind.HARD),
    (231000, 231000, AnkiVersionKind.TESTED),
    (0, None, AnkiVersionKind.UNKNOWN),
    (None, None, AnkiVersionKind.UNKNOWN),
])
def test_from_manifest_max(max_point_version: int | None, point: int | None, kind: AnkiVersionKind):
    assert AnkiVersionCodec.from_manifest_max(max_point_version) == (point, kind)
