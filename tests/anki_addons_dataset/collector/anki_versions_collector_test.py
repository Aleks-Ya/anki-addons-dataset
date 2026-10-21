import json
from pathlib import Path
from unittest.mock import Mock

from anki_addons_dataset.collector.anki_versions_collector import AnkiVersionsCollector
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.common.data_types import AnkiPointVersion, AnkiRelease, AnkiVersion
from anki_addons_dataset.common.working_dir import SnapshotDir


def test_to_releases_keeps_stable_from_2_1_0_newest_first():
    tag_names: list[str] = ["1.2.11", "2.0.52", "2.1.0", "2.1.0beta1", "2.1.66", "23.10", "23.10rc1",
                            "25.09.2", "25.09.2", "26.05b1", "test-tag"]
    assert AnkiVersionsCollector.to_releases(tag_names) == [
        AnkiRelease(AnkiVersion("25.09.2"), AnkiPointVersion(250902)),
        AnkiRelease(AnkiVersion("23.10"), AnkiPointVersion(231000)),
        AnkiRelease(AnkiVersion("2.1.66"), AnkiPointVersion(66)),
        AnkiRelease(AnkiVersion("2.1.0"), AnkiPointVersion(0))]


def test_to_releases_empty():
    assert AnkiVersionsCollector.to_releases([]) == []


def test_download(snapshot_dir: SnapshotDir):
    github_service: GithubService = Mock()
    github_service.get_tag_names = Mock(return_value=["2.1.66"])
    AnkiVersionsCollector(github_service).download()
    github_service.get_tag_names.assert_called_once_with(AnkiVersionsCollector.anki_repo)


def test_read_missing_raw(snapshot_dir: SnapshotDir):
    assert AnkiVersionsCollector.read(snapshot_dir) is None


def test_read(snapshot_dir: SnapshotDir):
    __write_raw(snapshot_dir, [{"ref": "refs/tags/2.1.66"}, {"ref": "refs/tags/25.09.2"},
                               {"ref": "refs/tags/25.09rc1"}])
    assert AnkiVersionsCollector.read(snapshot_dir) == [
        AnkiRelease(AnkiVersion("25.09.2"), AnkiPointVersion(250902)),
        AnkiRelease(AnkiVersion("2.1.66"), AnkiPointVersion(66))]


def test_read_not_found(snapshot_dir: SnapshotDir):
    __write_raw(snapshot_dir, {})
    assert AnkiVersionsCollector.read(snapshot_dir) == []


def __write_raw(snapshot_dir: SnapshotDir, content: object) -> None:
    raw_file: Path = snapshot_dir.get_raw_dir() / "2-github" / "ankitects" / "anki" / "tags.json"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text(json.dumps(content))
