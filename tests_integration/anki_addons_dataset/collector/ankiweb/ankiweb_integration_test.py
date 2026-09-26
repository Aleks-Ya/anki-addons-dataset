from pathlib import Path

import pytest

from anki_addons_dataset.collector.ankiweb.addon_page_downloader import AddonPageDownloader
from anki_addons_dataset.collector.ankiweb.addon_page_parser import AddonPageParser
from anki_addons_dataset.collector.ankiweb.addons_page_downloader import AddonsPageDownloader
from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonHeader, AddonId, AddonInfo, GithubRepo, SnapshotDate, TopicId, \
    TopicSlug
from anki_addons_dataset.common.working_dir import SnapshotDir

MIN_EXPECTED_ADDONS: int = 500


@pytest.fixture(scope="module")
def snapshot_dir(tmp_path_factory: pytest.TempPathFactory, snapshot_date: SnapshotDate) -> SnapshotDir:
    base: Path = tmp_path_factory.mktemp("ankiweb")
    return SnapshotDir(base / "history" / snapshot_date.isoformat()).create()


@pytest.fixture(scope="module")
def addon_headers(page_downloader: PageDownloader, snapshot_dir: SnapshotDir) -> list[AddonHeader]:
    downloader: AddonsPageDownloader = AddonsPageDownloader(page_downloader, snapshot_dir, offline=False)
    return downloader.get_headers()


def test_download_addons_page(addon_headers: list[AddonHeader], snapshot_dir: SnapshotDir) -> None:
    assert len(addon_headers) > MIN_EXPECTED_ADDONS
    for header in addon_headers:
        assert header.id > 0
        assert header.title
        assert header.addon_page_url == f"https://ankiweb.net/shared/info/{header.id}"
        assert header.update_date
    raw_file: Path = snapshot_dir.get_raw_dir() / "1-anki-web" / "addons_page.html"
    assert raw_file.exists()
    assert raw_file.stat().st_size > 0


def test_download_known_addon_page(page_downloader: PageDownloader, snapshot_dir: SnapshotDir,
                                   addon_headers: list[AddonHeader], known_addon_id: AddonId,
                                   known_github_repo: GithubRepo, known_topic_slug: TopicSlug,
                                   known_topic_id: TopicId) -> None:
    header: AddonHeader = __find_header(addon_headers, known_addon_id)
    addon_page_parser: AddonPageParser = AddonPageParser(Overrider(snapshot_dir))
    downloader: AddonPageDownloader = AddonPageDownloader(
        page_downloader, snapshot_dir, addon_page_parser, offline=False)

    addon_info: AddonInfo = downloader.get_addon_info(header)

    assert addon_info.header == header
    assert addon_info.page.content
    assert addon_info.page.description
    assert addon_info.page.branches
    assert addon_info.github is not None
    assert addon_info.github.github_repo is not None
    assert addon_info.github.github_repo.get_id().lower() == known_github_repo.get_id().lower()
    assert addon_info.forum is not None
    assert addon_info.forum.anki_forum_url == f"https://forums.ankiweb.net/t/{known_topic_slug}/{known_topic_id}"
    assert (snapshot_dir.get_raw_dir() / "1-anki-web" / "addon" / f"{known_addon_id}.html").exists()
    assert (snapshot_dir.get_stage_dir() / "1-anki-web" / "addon" / f"{known_addon_id}.json").exists()


def __find_header(addon_headers: list[AddonHeader], addon_id: AddonId) -> AddonHeader:
    for header in addon_headers:
        if header.id == addon_id:
            return header
    raise AssertionError(f"Addon {addon_id} is no longer listed on AnkiWeb: pick another known addon")
