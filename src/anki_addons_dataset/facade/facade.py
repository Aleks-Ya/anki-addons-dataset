import shutil
from datetime import date
from pathlib import Path

from anki_addons_dataset.aggregator.aggregator import Aggregator
from anki_addons_dataset.collector.addon_collector import AddonCollector
from anki_addons_dataset.collector.ankiweb.addon_page_parser import AddonPageParser
from anki_addons_dataset.collector.ankiweb.ankiweb_service import AnkiWebService
from anki_addons_dataset.collector.enricher.enricher import Enricher
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonInfo, Aggregation
from anki_addons_dataset.exporter.exporter_facade import ExporterFacade
from anki_addons_dataset.huggingface.hugging_face import HuggingFace


class Facade:

    def __init__(self, working_dir: Path):
        self.__working_dir: Path = working_dir
        self.__history_dir: Path = self.__working_dir / "history"

    def create_datasets(self, offline: bool) -> None:
        for history_sub_dir in self.__history_dir.iterdir():
            if history_sub_dir.is_dir():
                creation_date: date = date.fromisoformat(history_sub_dir.name)
                self.create_dataset(creation_date, offline)
            else:
                print(f"Skipping {history_sub_dir}")

    def create_dataset(self, creation_date: date, offline: bool) -> None:
        print(f"===== Creating dataset for {creation_date} =====")
        print(f"Offline: {offline}")
        version_dir: Path = self.__history_dir / f"{creation_date.isoformat()}"
        final_dir: Path = version_dir / "final"
        print(f"Final dir: {final_dir}")
        raw_dir: Path = version_dir / "raw"
        print(f"Raw dir: {raw_dir}")
        stage_dir: Path = version_dir / "stage"
        print(f"Stage dir: {stage_dir}")
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

        hugging_face: HuggingFace = HuggingFace(final_dir, creation_date)
        hugging_face.create_dataset_card()
        hugging_face.create_metadata_yaml()

        print(f"===== Created dataset for {creation_date} =====\n")

    @staticmethod
    def __delete_dir(directory: Path) -> None:
        print(f"Deleting dir: {directory}")
        shutil.rmtree(directory, ignore_errors=True)
