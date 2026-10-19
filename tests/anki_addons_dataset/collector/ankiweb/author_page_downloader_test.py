from pathlib import Path
from unittest.mock import Mock

from anki_addons_dataset.collector.ankiweb.author_page_downloader import AuthorPageDownloader
from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.common.data_types import AddonId, HtmlStr
from anki_addons_dataset.common.working_dir import SnapshotDir

__html: HtmlStr = HtmlStr('<html><body><main><ul><li><a href="/shared/info/2">B</a></li>'
                          '<li><a href="/shared/info/1">A</a></li></ul></main></body></html>')


def __author_file(snapshot_dir: SnapshotDir, addon_id: int) -> Path:
    return snapshot_dir.get_raw_dir() / "1-anki-web" / "by-author" / f"{addon_id}.html"


def test_downloads_and_caches_the_author_page(page_downloader: PageDownloader, snapshot_dir: SnapshotDir):
    page_downloader.load_page = Mock(return_value=__html)
    downloader: AuthorPageDownloader = AuthorPageDownloader(page_downloader, snapshot_dir, False)

    assert downloader.has_author_pages() is True
    assert downloader.get_author_item_ids(AddonId(1)) == [AddonId(1), AddonId(2)]
    assert downloader.get_author_item_ids(AddonId(1)) == [AddonId(1), AddonId(2)]

    page_downloader.load_page.assert_called_once()
    assert page_downloader.load_page.call_args.args[0] == "https://ankiweb.net/shared/by-author/1"
    assert __author_file(snapshot_dir, 1).read_text() == __html


def test_redownloads_an_empty_file(page_downloader: PageDownloader, snapshot_dir: SnapshotDir):
    page_downloader.load_page = Mock(return_value=__html)
    downloader: AuthorPageDownloader = AuthorPageDownloader(page_downloader, snapshot_dir, False)
    __author_file(snapshot_dir, 1).write_text("")

    assert downloader.get_author_item_ids(AddonId(1)) == [AddonId(1), AddonId(2)]
    page_downloader.load_page.assert_called_once()


def test_a_failed_download_is_skipped(page_downloader: PageDownloader, snapshot_dir: SnapshotDir):
    page_downloader.load_page = Mock(side_effect=TimeoutError("no items"))
    downloader: AuthorPageDownloader = AuthorPageDownloader(page_downloader, snapshot_dir, False)

    assert downloader.get_author_item_ids(AddonId(1)) is None
    assert not __author_file(snapshot_dir, 1).exists()


def test_offline_reads_only_the_cache(page_downloader: PageDownloader, snapshot_dir: SnapshotDir):
    page_downloader.load_page = Mock()
    downloader: AuthorPageDownloader = AuthorPageDownloader(page_downloader, snapshot_dir, True)
    assert downloader.has_author_pages() is False

    __author_file(snapshot_dir, 1).parent.mkdir(parents=True)
    __author_file(snapshot_dir, 1).write_text(__html)

    assert downloader.has_author_pages() is True
    assert downloader.get_author_item_ids(AddonId(1)) == [AddonId(1), AddonId(2)]
    assert downloader.get_author_item_ids(AddonId(3)) is None
    page_downloader.load_page.assert_not_called()
