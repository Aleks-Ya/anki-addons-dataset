import logging
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Optional

from pydiscourse import DiscourseClient

from anki_addons_dataset.collector.aggregator import Aggregator
from anki_addons_dataset.collector.addon_infos_collector import AddonInfosCollector
from anki_addons_dataset.collector.ankiforum.ankiforum_enricher import AnkiForumEnricher
from anki_addons_dataset.collector.ankiforum.ankiforum_service import AnkiForumService
from anki_addons_dataset.collector.ankiweb.addon_page_downloader import AddonPageDownloader
from anki_addons_dataset.collector.ankiweb.addon_page_parser import AddonPageParser
from anki_addons_dataset.collector.ankiweb.addons_page_downloader import AddonsPageDownloader
from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.collector.dataset_metadata import DatasetMetadata
from anki_addons_dataset.collector.github.github_enricher import GithubEnricher
from anki_addons_dataset.collector.github.github_rest_client import GithubRestClient
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import Aggregation, AddonInfos, DatasetSnapshotMetadata, RawMetadata, \
    SnapshotDate, ReportDate
from anki_addons_dataset.collector.ankiweb.ankiweb_service import AnkiWebService
from anki_addons_dataset.common.working_dir import SnapshotDir, WorkingDir
from anki_addons_dataset.exporter.exporter_facade import ExporterFacade
from anki_addons_dataset.collector.raw_metadata_collector import RawMetadataCollector

log: Logger = logging.getLogger(__name__)


class CollectorFacade:
    def __init__(self, working_dir: WorkingDir):
        self.__working_dir: WorkingDir = working_dir

    def download_snapshot(self, snapshot_date: Optional[SnapshotDate]) -> None:
        log.info(f"===== Download dataset for {snapshot_date} =====")
        if not snapshot_date:
            raise ValueError("Snapshot date is required")
        snapshot_dir: SnapshotDir = self.__working_dir.get_snapshot_dir(snapshot_date).create()
        script_version: str = self.__script_version()
        raw_metadata_collector: RawMetadataCollector = RawMetadataCollector(snapshot_dir)
        if not raw_metadata_collector.read_metadata().start_timestamp:
            raw_metadata_collector.set_script_version(script_version)
            raw_metadata_collector.set_start_datetime(datetime.now().replace(microsecond=0))
        self.__collect(snapshot_dir, False)
        if not raw_metadata_collector.read_metadata().finish_timestamp:
            raw_metadata_collector.set_finish_datetime(datetime.now().replace(microsecond=0))
        log.info(f"===== Downloaded snapshot for {snapshot_date} =====\n")

    def parse_snapshots(self, report_date: ReportDate) -> None:
        for snapshot_dir in self.__working_dir.list_snapshot_dirs():
            snapshot_date: SnapshotDate = snapshot_dir.snapshot_dir_to_snapshot_date()
            self.__parse_snapshot(snapshot_date, report_date)

    def __parse_snapshot(self, snapshot_date: SnapshotDate, report_date: ReportDate) -> None:
        log.info(f"===== Parse snapshot for {snapshot_date} =====")
        snapshot_dir: SnapshotDir = self.__working_dir.get_snapshot_dir(snapshot_date).create()
        script_version: str = self.__script_version()
        addon_infos: AddonInfos = self.__collect(snapshot_dir, True)
        aggregation: Aggregation = Aggregator.aggregate(addon_infos)
        exporter_facade: ExporterFacade = ExporterFacade(snapshot_dir)
        dataset_snapshot_metadata: DatasetSnapshotMetadata = DatasetMetadata.create_dataset_snapshot_metadata(
            snapshot_dir, script_version, report_date)
        DatasetMetadata.write_snapshot_metadata_to_json(snapshot_dir, dataset_snapshot_metadata)
        raw_metadata_collector: RawMetadataCollector = RawMetadataCollector(snapshot_dir)
        raw_metadata: RawMetadata = raw_metadata_collector.read_metadata()
        exporter_facade.export_all(addon_infos, aggregation, dataset_snapshot_metadata, raw_metadata)
        log.info(f"===== Parsed snapshot for {snapshot_date} =====\n")

    @staticmethod
    def __script_version() -> str:
        version_file: Path = Path(__file__).parent.parent / "version.txt"
        return version_file.read_text().strip()

    @staticmethod
    def __collect(snapshot_dir: SnapshotDir, offline: bool) -> AddonInfos:
        log.info(f"Offline: {offline}")
        overrider: Overrider = Overrider(snapshot_dir)
        addon_page_parser: AddonPageParser = AddonPageParser(overrider)
        page_downloader: PageDownloader = PageDownloader()
        addons_page_downloader: AddonsPageDownloader = AddonsPageDownloader(page_downloader, snapshot_dir, offline)
        addon_page_downloader: AddonPageDownloader = AddonPageDownloader(
            page_downloader, snapshot_dir, addon_page_parser, offline)
        ankiweb_service: AnkiWebService = AnkiWebService(addons_page_downloader, addon_page_downloader)
        github_rest_client: GithubRestClient = GithubRestClient(offline)
        github_service: GithubService = GithubService(snapshot_dir, github_rest_client)
        discourse_client: DiscourseClient = DiscourseClient(host="https://forums.ankiweb.net",
                                                            api_username=None, api_key=None)
        anki_forum_service: AnkiForumService = AnkiForumService(discourse_client, snapshot_dir, offline)
        github_enricher: GithubEnricher = GithubEnricher(snapshot_dir, github_service)
        anki_forum_enricher: AnkiForumEnricher = AnkiForumEnricher(snapshot_dir, anki_forum_service)
        addon_infos_collector: AddonInfosCollector = AddonInfosCollector(
            ankiweb_service, github_enricher, anki_forum_enricher, overrider)
        return addon_infos_collector.collect_addons()
