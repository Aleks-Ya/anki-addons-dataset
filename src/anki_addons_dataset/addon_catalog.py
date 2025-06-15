import shutil
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

if __name__ == "__main__":
    working_dir: Path = Path.home() / "anki-addons-dataset"
    dataset_dir: Path = working_dir / "dataset"
    cache_dir: Path = working_dir / "cache"
    shutil.rmtree(dataset_dir, ignore_errors=True)
    overrider: Overrider = Overrider(dataset_dir)
    addon_page_parser: AddonPageParser = AddonPageParser(overrider)
    ankiweb_service: AnkiWebService = AnkiWebService(dataset_dir, cache_dir, addon_page_parser)
    github_service: GithubService = GithubService(dataset_dir, cache_dir)
    enricher: Enricher = Enricher(dataset_dir, github_service)
    collector: AddonCollector = AddonCollector(ankiweb_service, enricher, overrider)
    addon_infos: list[AddonInfo] = collector.collect_addons()

    aggregation: Aggregation = Aggregator.aggregate(addon_infos)

    exporter_facade: ExporterFacade = ExporterFacade(dataset_dir)
    exporter_facade.export_all(addon_infos, aggregation)

    dataset_metadata_file: Path = Path(__file__).parent / "dataset-metadata.json"
    dest_dataset_metadata_file: Path = dataset_dir / "dataset-metadata.json"
    shutil.copy(dataset_metadata_file, dest_dataset_metadata_file)
