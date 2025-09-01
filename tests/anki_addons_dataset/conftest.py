import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import Mock

from pytest import fixture

from anki_addons_dataset.collector.ankiweb.addon_page_downloader import AddonPageDownloader
from anki_addons_dataset.collector.ankiweb.addon_page_parser import AddonPageParser
from anki_addons_dataset.collector.ankiweb.addons_page_downloader import AddonsPageDownloader
from anki_addons_dataset.collector.ankiweb.ankiweb_service import AnkiWebService
from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonId
from anki_addons_dataset.common.working_dir import WorkingDir, VersionDir


@fixture
def working_dir_path() -> Path:
    return Path(tempfile.mkdtemp())


@fixture
def working_dir(working_dir_path: Path) -> WorkingDir:
    return WorkingDir(working_dir_path)


@fixture
def version_dir(working_dir: WorkingDir) -> VersionDir:
    return working_dir.get_version_dir(date.fromisoformat("2025-01-25")).create()


@fixture
def overrider(version_dir: VersionDir) -> Overrider:
    return Overrider(version_dir)


@fixture
def note_size_addon_id() -> AddonId:
    return AddonId(1188705668)


@fixture
def hyper_tts_addon_id() -> AddonId:
    return AddonId(111623432)


@fixture
def page_downloader() -> PageDownloader:
    return Mock()


@fixture
def addon_page_parser(overrider: Overrider) -> AddonPageParser:
    return AddonPageParser(overrider)


@fixture
def offline() -> bool:
    return False


@fixture
def addons_page_downloader(page_downloader: PageDownloader, version_dir: VersionDir,
                           offline: bool) -> AddonsPageDownloader:
    return AddonsPageDownloader(page_downloader, version_dir, offline)


@fixture
def addon_page_downloader(page_downloader: PageDownloader, version_dir: VersionDir,
                          addon_page_parser: AddonPageParser, offline: bool) -> AddonPageDownloader:
    return AddonPageDownloader(page_downloader, version_dir, addon_page_parser, offline)


@fixture
def ankiweb_service(addons_page_downloader: AddonsPageDownloader,
                    addon_page_downloader: AddonPageDownloader) -> AnkiWebService:
    return AnkiWebService(addons_page_downloader, addon_page_downloader)
