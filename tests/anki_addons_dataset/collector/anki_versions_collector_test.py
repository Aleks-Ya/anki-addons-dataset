import json
import logging
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from anki_addons_dataset.collector.anki_versions_collector import AnkiVersionsCollector
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.common.data_types import AnkiPointVersion, AnkiRelease, AnkiVersion, GithubRelease
from anki_addons_dataset.common.working_dir import SnapshotDir


def test_to_releases_keeps_stable_from_2_1_0_newest_first():
    tag_names: list[str] = ["1.2.11", "2.0.52", "2.1.0", "2.1.0beta1", "2.1.66", "23.10", "23.10rc1",
                            "25.09.2", "25.09.2", "26.05b1", "test-tag"]
    assert AnkiVersionsCollector.to_releases(tag_names, []) == [
        AnkiRelease(AnkiVersion("25.09.2"), AnkiPointVersion(250902)),
        AnkiRelease(AnkiVersion("23.10"), AnkiPointVersion(231000)),
        AnkiRelease(AnkiVersion("2.1.66"), AnkiPointVersion(66)),
        AnkiRelease(AnkiVersion("2.1.0"), AnkiPointVersion(0))]


def test_to_releases_empty():
    assert AnkiVersionsCollector.to_releases([], []) == []


def test_to_releases_takes_dates_from_github_releases():
    github_releases: list[GithubRelease] = [
        __github_release("26.09.1", datetime(2026, 9, 15, 19, 47, 37), True),
        __github_release("26.09b1", datetime(2026, 9, 1, 10, 0, 0), True),
        __github_release("25.09", None, False)]
    assert AnkiVersionsCollector.to_releases(["26.09.1", "26.09b1", "25.09", "2.1.66"], github_releases) == [
        AnkiRelease(AnkiVersion("26.09.1"), AnkiPointVersion(260901), date(2026, 9, 15)),
        AnkiRelease(AnkiVersion("25.09"), AnkiPointVersion(250900)),
        AnkiRelease(AnkiVersion("2.1.66"), AnkiPointVersion(66))]


def test_download(snapshot_dir: SnapshotDir):
    github_service: GithubService = Mock()
    github_service.get_tag_names = Mock(return_value=["2.1.66"])
    github_service.get_releases = Mock(return_value=None)
    AnkiVersionsCollector(github_service).download()
    github_service.get_tag_names.assert_called_once_with(AnkiVersionsCollector.anki_repo)
    github_service.get_releases.assert_called_once_with(AnkiVersionsCollector.anki_repo)


def test_read_missing_raw(snapshot_dir: SnapshotDir):
    assert AnkiVersionsCollector.read(snapshot_dir) is None


def test_read(snapshot_dir: SnapshotDir):
    __write_raw(snapshot_dir, "tags", [{"ref": "refs/tags/2.1.66"}, {"ref": "refs/tags/25.09.2"},
                                       {"ref": "refs/tags/25.09rc1"}])
    __write_raw(snapshot_dir, "releases", [{"tag_name": "25.09.2", "published_at": "2025-10-01T12:30:00Z"},
                                           {"tag_name": "25.09rc1", "published_at": "2025-09-01T12:30:00Z"}])
    assert AnkiVersionsCollector.read(snapshot_dir) == [
        AnkiRelease(AnkiVersion("25.09.2"), AnkiPointVersion(250902), date(2025, 10, 1)),
        AnkiRelease(AnkiVersion("2.1.66"), AnkiPointVersion(66))]


def test_read_missing_releases_warns_and_leaves_dates_empty(snapshot_dir: SnapshotDir,
                                                            caplog: pytest.LogCaptureFixture):
    __write_raw(snapshot_dir, "tags", [{"ref": "refs/tags/25.09.2"}])
    with caplog.at_level(logging.WARNING):
        act: list[AnkiRelease] = AnkiVersionsCollector.read(snapshot_dir)
    assert act == [AnkiRelease(AnkiVersion("25.09.2"), AnkiPointVersion(250902))]
    assert "the anki_versions table has no release dates" in caplog.text


def test_read_not_found(snapshot_dir: SnapshotDir):
    __write_raw(snapshot_dir, "tags", {})
    assert AnkiVersionsCollector.read(snapshot_dir) == []


def test_read_releases_not_found(snapshot_dir: SnapshotDir):
    __write_raw(snapshot_dir, "tags", [{"ref": "refs/tags/25.09.2"}])
    __write_raw(snapshot_dir, "releases", {})
    assert AnkiVersionsCollector.read(snapshot_dir) == [AnkiRelease(AnkiVersion("25.09.2"), AnkiPointVersion(250902))]


def __github_release(tag_name: str, published_at: datetime | None, prerelease: bool) -> GithubRelease:
    return GithubRelease(tag_name=tag_name, name=None, published_at=published_at, prerelease=prerelease, assets=[])


def __write_raw(snapshot_dir: SnapshotDir, filename: str, content: object) -> None:
    raw_file: Path = snapshot_dir.get_raw_dir() / "2-github" / "ankitects" / "anki" / f"{filename}.json"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text(json.dumps(content))
