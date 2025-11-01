from datetime import date, datetime
from pathlib import Path
import logging
from logging import Logger

from anki_addons_dataset.aggregator.aggregator import Aggregator
from anki_addons_dataset.argument.script_arguments import Operation
from anki_addons_dataset.bundle.dataset_bundle import DatasetBundle
from anki_addons_dataset.collector.addon_collector import AddonCollector
from anki_addons_dataset.collector.ankiweb.addon_page_downloader import AddonPageDownloader
from anki_addons_dataset.collector.ankiweb.addon_page_parser import AddonPageParser
from anki_addons_dataset.collector.ankiweb.addons_page_downloader import AddonsPageDownloader
from anki_addons_dataset.collector.ankiweb.ankiweb_service import AnkiWebService
from anki_addons_dataset.collector.ankiweb.page_downloader import PageDownloader
from anki_addons_dataset.collector.enricher.enricher import Enricher
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonInfo, Aggregation
from anki_addons_dataset.common.working_dir import WorkingDir, VersionDir
from anki_addons_dataset.exporter.exporter_facade import ExporterFacade
from anki_addons_dataset.facade.raw_metadata import RawMetadata
from anki_addons_dataset.huggingface.hugging_face import HuggingFace

log: Logger = logging.getLogger(__name__)


class Facade:

    def __init__(self, working_dir: WorkingDir):
        self.__working_dir: WorkingDir = working_dir

    def process(self, operation: Operation, creation_date: date) -> None:
        if operation == Operation.DOWNLOAD:
            self.__download_operation(creation_date)
        elif operation == Operation.PARSE:
            self.__parse_operation()
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    def __download_operation(self, creation_date: date) -> None:
        self.__download_version(creation_date)

    def __parse_operation(self) -> None:
        for version_dir in self.__working_dir.list_version_dirs():
            creation_date: date = version_dir.version_dir_to_creation_date()
            self.__parse_version(creation_date)
        dataset_bundle: DatasetBundle = DatasetBundle(self.__working_dir)
        dataset_bundle.create_bundle()

    def __download_version(self, creation_date: date) -> None:
        log.info(f"===== Download dataset for {creation_date} =====")
        offline: bool = False
        log.info(f"Offline: {offline}")
        version_dir: VersionDir = self.__working_dir.get_version_dir(creation_date).create()
        script_version: str = self.__script_version()
        raw_metadata: RawMetadata = RawMetadata(version_dir)
        if not raw_metadata.get_start_datetime():
            raw_metadata.set_script_version(script_version)
            raw_metadata.set_start_datetime(datetime.now().replace(microsecond=0))
        overrider: Overrider = Overrider(version_dir)
        addon_page_parser: AddonPageParser = AddonPageParser(overrider)
        ankiweb_sleep_sec: int = 3
        page_downloader: PageDownloader = PageDownloader(ankiweb_sleep_sec)
        addons_page_downloader: AddonsPageDownloader = AddonsPageDownloader(page_downloader, version_dir, offline)
        addon_page_downloader: AddonPageDownloader = AddonPageDownloader(
            page_downloader, version_dir, addon_page_parser, offline)
        ankiweb_service: AnkiWebService = AnkiWebService(addons_page_downloader, addon_page_downloader)
        github_sleep_sec: int = 1
        github_service: GithubService = GithubService(version_dir, github_sleep_sec, offline)
        enricher: Enricher = Enricher(version_dir, github_service)
        collector: AddonCollector = AddonCollector(ankiweb_service, enricher, overrider)
        collector.collect_addons()
        if not raw_metadata.get_finish_datetime():
            raw_metadata.set_finish_datetime(datetime.now().replace(microsecond=0))
        log.info(f"===== Downloaded dataset for {creation_date} =====\n")

    def __parse_version(self, creation_date: date) -> None:
        offline: bool = True
        log.info(f"===== Parse dataset for {creation_date} =====")
        log.info(f"Offline: {offline}")
        version_dir: VersionDir = self.__working_dir.get_version_dir(creation_date).create()
        script_version: str = self.__script_version()
        overrider: Overrider = Overrider(version_dir)
        addon_page_parser: AddonPageParser = AddonPageParser(overrider)
        ankiweb_sleep_sec: int = 3
        page_downloader: PageDownloader = PageDownloader(ankiweb_sleep_sec)
        addons_page_downloader: AddonsPageDownloader = AddonsPageDownloader(page_downloader, version_dir, offline)
        addon_page_downloader: AddonPageDownloader = AddonPageDownloader(
            page_downloader, version_dir, addon_page_parser, offline)
        ankiweb_service: AnkiWebService = AnkiWebService(addons_page_downloader, addon_page_downloader)
        github_sleep_sec: int = 1
        github_service: GithubService = GithubService(version_dir, github_sleep_sec, offline)
        enricher: Enricher = Enricher(version_dir, github_service)
        collector: AddonCollector = AddonCollector(ankiweb_service, enricher, overrider)
        addon_infos: list[AddonInfo] = collector.collect_addons()

        aggregation: Aggregation = Aggregator.aggregate(addon_infos)

        exporter_facade: ExporterFacade = ExporterFacade(version_dir)
        exporter_facade.export_all(addon_infos, aggregation)

        HuggingFace.create_version_metadata_yaml(version_dir, script_version)

        log.info(f"===== Parsed dataset for {creation_date} =====\n")

    @staticmethod
    def __script_version() -> str:
        version_file: Path = Path(__file__).parent.parent / "version.txt"
        return version_file.read_text().strip()
