import shutil
from datetime import date, datetime
from pathlib import Path

from anki_addons_dataset.aggregator.aggregator import Aggregator
from anki_addons_dataset.bundle.dataset_bundle import DatasetBundle
from anki_addons_dataset.collector.addon_collector import AddonCollector
from anki_addons_dataset.collector.ankiweb.addon_page_parser import AddonPageParser
from anki_addons_dataset.collector.ankiweb.ankiweb_service import AnkiWebService
from anki_addons_dataset.collector.enricher.enricher import Enricher
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonInfo, Aggregation
from anki_addons_dataset.common.working_dir import WorkingDir, VersionDir
from anki_addons_dataset.exporter.exporter_facade import ExporterFacade
from anki_addons_dataset.facade.version_metadata import VersionMetadata
from anki_addons_dataset.huggingface.hugging_face import HuggingFace


class Facade:

    def __init__(self, working_dir: WorkingDir):
        self.__working_dir: WorkingDir = working_dir

    def create_datasets(self, offline: bool) -> None:
        for version_dir in self.__working_dir.list_version_dirs():
            creation_date: date = version_dir.version_dir_to_creation_date()
            self.__create_dataset(creation_date, offline)
        dataset_bundle: DatasetBundle = DatasetBundle(self.__working_dir)
        dataset_bundle.create_bundle()

    def __create_dataset(self, creation_date: date, offline: bool) -> None:
        print(f"===== Creating dataset for {creation_date} =====")
        print(f"Offline: {offline}")
        version_dir: VersionDir = self.__working_dir.get_version_dir(creation_date)
        version_metadata: VersionMetadata = VersionMetadata(version_dir)
        script_version: str = self.__script_version()
        if not version_metadata.get_start_datetime():
            version_metadata.set_script_version(script_version)
            version_metadata.set_start_datetime(datetime.now().replace(microsecond=0))
        raw_dir: Path = version_dir.get_raw_dir()
        print(f"Raw dir: {raw_dir}")
        stage_dir: Path = version_dir.get_stage_dir()
        print(f"Stage dir: {stage_dir}")
        final_dir: Path = version_dir.get_final_dir()
        print(f"Final dir: {final_dir}")
        self.__delete_dir(stage_dir)
        self.__delete_dir(final_dir)
        overrider: Overrider = Overrider(stage_dir)
        addon_page_parser: AddonPageParser = AddonPageParser(overrider)
        ankiweb_service: AnkiWebService = AnkiWebService(raw_dir, stage_dir, addon_page_parser, offline)
        github_service: GithubService = GithubService(raw_dir, stage_dir, offline)
        enricher: Enricher = Enricher(stage_dir, github_service)
        collector: AddonCollector = AddonCollector(ankiweb_service, enricher, overrider)
        addon_infos: list[AddonInfo] = collector.collect_addons()

        aggregation: Aggregation = Aggregator.aggregate(addon_infos)

        exporter_facade: ExporterFacade = ExporterFacade(final_dir)
        exporter_facade.export_all(addon_infos, aggregation)

        HuggingFace.create_version_metadata_yaml(version_dir, script_version)

        if not version_metadata.get_finish_datetime():
            version_metadata.set_finish_datetime(datetime.now().replace(microsecond=0))

        print(f"===== Created dataset for {creation_date} =====\n")

    @staticmethod
    def __delete_dir(directory: Path) -> None:
        print(f"Deleting dir: {directory}")
        shutil.rmtree(directory, ignore_errors=True)

    @staticmethod
    def __script_version() -> str:
        version_file: Path = Path(__file__).parent.parent / "version.txt"
        return version_file.read_text().strip()
