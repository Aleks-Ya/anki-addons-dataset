import logging
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Optional

from pydiscourse import DiscourseClient

from anki_addons_dataset.collector.aggregator import Aggregator
from anki_addons_dataset.collector.addon_infos_collector import AddonInfosCollector
from anki_addons_dataset.collector.ai.ai_cache_index import AiCacheIndex
from anki_addons_dataset.collector.ai.ai_cache_stats import AiCacheStats
from anki_addons_dataset.collector.ai.ai_enricher import AiEnricher
from anki_addons_dataset.collector.ai.ai_provider import AiProvider
from anki_addons_dataset.collector.ai.ai_summarizer import AiSummarizer
from anki_addons_dataset.collector.ai.cached_ai_provider import CachedAiProvider
from anki_addons_dataset.collector.ai.deepseek_ai_provider import DeepSeekAiProvider
from anki_addons_dataset.collector.ai.no_ai_provider import NoAiProvider
from anki_addons_dataset.collector.ai.openai_ai_provider import OpenAiAiProvider
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
    SnapshotDate, ReportDate, ScriptVersion, PageLoadTimeout, ElementWaitTimeout, AiModel
from anki_addons_dataset.collector.ankiweb.ankiweb_service import AnkiWebService
from anki_addons_dataset.common.json_helper import JsonHelper
from anki_addons_dataset.common.working_dir import SnapshotDir, WorkingDir
from anki_addons_dataset.config.app_config import AppConfig
from anki_addons_dataset.exporter.exporter_facade import ExporterFacade
from anki_addons_dataset.collector.raw_metadata_collector import RawMetadataCollector
from anki_addons_dataset.collector.sample_collector import SampleCollector

log: Logger = logging.getLogger(__name__)


class CollectorFacade:
    def __init__(self, working_dir: WorkingDir, config: AppConfig, page_load_timeout: PageLoadTimeout,
                 element_wait_timeout: ElementWaitTimeout):
        self.__working_dir: WorkingDir = working_dir
        self.__config: AppConfig = config
        self.__page_load_timeout: PageLoadTimeout = page_load_timeout
        self.__element_wait_timeout: ElementWaitTimeout = element_wait_timeout

    def download_snapshot(self, snapshot_date: Optional[SnapshotDate]) -> None:
        log.info(f"===== Download dataset for {snapshot_date} =====")
        if not snapshot_date:
            raise ValueError("Snapshot date is required")
        snapshot_dir: SnapshotDir = self.__working_dir.get_snapshot_dir(snapshot_date).create()
        prev_snapshot_dir: Optional[SnapshotDir] = self.__working_dir.get_previous_snapshot_dir(snapshot_date)
        script_version: ScriptVersion = self.__script_version()
        raw_metadata_collector: RawMetadataCollector = RawMetadataCollector(snapshot_dir)
        if not raw_metadata_collector.read_metadata().start_timestamp:
            raw_metadata_collector.set_script_version(script_version)
            raw_metadata_collector.set_start_datetime(datetime.now().replace(microsecond=0))
        self.__collect(snapshot_dir, False, prev_snapshot_dir)
        SampleCollector(snapshot_dir).set_addons(self.__config.sample.addons)
        if not raw_metadata_collector.read_metadata().finish_timestamp:
            raw_metadata_collector.set_finish_datetime(datetime.now().replace(microsecond=0))
        log.info(f"===== Downloaded snapshot for {snapshot_date} =====\n")

    def summarize_snapshots(self) -> None:
        # Answers are shared across the whole history, not just carried forward from the previous snapshot:
        # the cache key is a hash of the model and the prompt, so an identical prompt has an identical answer.
        # list_snapshot_dirs(), not the sampled variant, so sampling cannot hide answers from the lookup.
        shared_index: AiCacheIndex = AiCacheIndex.load(
            [snapshot_dir.get_ai_cache_file() for snapshot_dir in self.__working_dir.list_snapshot_dirs()])
        log.info(f"AI cache holds {shared_index.size()} answers across all snapshots")
        total_stats: AiCacheStats = AiCacheStats()
        for snapshot_dir in self.__working_dir.list_sampled_snapshot_dirs():
            total_stats = total_stats + self.__summarize_snapshot(snapshot_dir, shared_index)
        log.info(f"Total AI cache hits: {total_stats.hit_count}, misses: {total_stats.miss_count}")

    def __summarize_snapshot(self, snapshot_dir: SnapshotDir, shared_index: AiCacheIndex) -> AiCacheStats:
        snapshot_date: SnapshotDate = snapshot_dir.snapshot_dir_to_snapshot_date()
        log.info(f"===== Summarize snapshot for {snapshot_date} =====")
        # No create(): this step only fills 1-raw, and wiping 3-final would discard an existing report.
        addon_infos: AddonInfos = self.__collect(snapshot_dir, True)
        ai_provider: CachedAiProvider = self.__ai_provider(snapshot_dir, False, shared_index)
        self.__ai_enricher(ai_provider).enrich(addon_infos)  # The filled cache is the result; PARSE reads it back
        stats: AiCacheStats = ai_provider.get_cache_stats()
        log.info(f"AI cache hits: {stats.hit_count}, misses: {stats.miss_count}")
        log.info(f"===== Summarized snapshot for {snapshot_date} =====\n")
        return stats

    def parse_snapshots(self) -> None:
        for snapshot_dir in self.__working_dir.list_sampled_snapshot_dirs():
            snapshot_date: SnapshotDate = snapshot_dir.snapshot_dir_to_snapshot_date()
            self.__parse_snapshot(snapshot_date)

    def __parse_snapshot(self, snapshot_date: SnapshotDate) -> None:
        log.info(f"===== Parse snapshot for {snapshot_date} =====")
        snapshot_dir: SnapshotDir = self.__working_dir.get_snapshot_dir(snapshot_date).create()
        script_version: ScriptVersion = self.__script_version()
        addon_infos: AddonInfos = self.__collect(snapshot_dir, True)
        ai_provider: CachedAiProvider = self.__ai_provider(snapshot_dir, True)
        addon_infos = self.__ai_enricher(ai_provider).enrich(addon_infos)
        cache_miss_count: int = ai_provider.get_cache_stats().miss_count
        if cache_miss_count:
            log.warning(f"{cache_miss_count} addons have no cached AI summary and stay without one. "
                        f"Run the 'ai' operation to fill the cache.")
        JsonHelper.write_addon_infos_dump(addon_infos, script_version, snapshot_dir.get_addon_infos_dump())
        log.info(f"===== Parsed snapshot for {snapshot_date} =====\n")

    def report_snapshots(self, report_date: ReportDate) -> None:
        for snapshot_dir in self.__working_dir.list_sampled_snapshot_dirs():
            snapshot_date: SnapshotDate = snapshot_dir.snapshot_dir_to_snapshot_date()
            self.__report_snapshot(snapshot_date, report_date)

    def __report_snapshot(self, snapshot_date: SnapshotDate, report_date: ReportDate) -> None:
        log.info(f"===== Report snapshot for {snapshot_date} =====")
        snapshot_dir: SnapshotDir = self.__working_dir.get_snapshot_dir(snapshot_date).create_final_dir()
        dump_file: Path = snapshot_dir.get_addon_infos_dump()
        if not dump_file.exists():
            raise FileNotFoundError(f"Missing parsed dump {dump_file}. Run the 'parse' operation first.")
        script_version, addon_infos = JsonHelper.read_addon_infos_dump(dump_file)
        current_script_version: ScriptVersion = self.__script_version()
        if script_version != current_script_version:
            log.warning(f"Dump was parsed with script version {script_version}, "
                        f"current version is {current_script_version}. Re-run 'parse' if the parsing logic changed.")
        aggregation: Aggregation = Aggregator.aggregate(addon_infos)
        exporter_facade: ExporterFacade = ExporterFacade(snapshot_dir)
        dataset_snapshot_metadata: DatasetSnapshotMetadata = DatasetMetadata.create_dataset_snapshot_metadata(
            snapshot_dir, script_version, report_date)
        DatasetMetadata.write_snapshot_metadata_to_json(snapshot_dir, dataset_snapshot_metadata)
        raw_metadata_collector: RawMetadataCollector = RawMetadataCollector(snapshot_dir)
        raw_metadata: RawMetadata = raw_metadata_collector.read_metadata()
        exporter_facade.export_all(addon_infos, aggregation, dataset_snapshot_metadata, raw_metadata)
        log.info(f"===== Reported snapshot for {snapshot_date} =====\n")

    def __ai_provider(self, snapshot_dir: SnapshotDir, offline: bool,
                      shared_index: Optional[AiCacheIndex] = None) -> CachedAiProvider:
        model: AiModel = AiModel(self.__config.ai.model)
        endpoint: str = self.__config.ai.endpoint
        online_provider_type: type[OpenAiAiProvider] = \
            DeepSeekAiProvider if DeepSeekAiProvider.owns(endpoint) else OpenAiAiProvider
        ai_provider: AiProvider = NoAiProvider(model) if offline else online_provider_type(
            endpoint, self.__config.ai.api_key_file.read_text().strip(), model)
        return CachedAiProvider(ai_provider, snapshot_dir.get_ai_cache_file(), shared_index, offline)

    def __ai_enricher(self, ai_provider: CachedAiProvider) -> AiEnricher:
        ai_summarizer: AiSummarizer = AiSummarizer(ai_provider, self.__config.ai.readme_max_chars)
        return AiEnricher(ai_summarizer, ai_provider.get_model())

    @staticmethod
    def __script_version() -> ScriptVersion:
        version_file: Path = Path(__file__).parent.parent / "version.txt"
        return ScriptVersion(version_file.read_text().strip())

    def __collect(self, snapshot_dir: SnapshotDir, offline: bool,
                  prev_snapshot_dir: Optional[SnapshotDir] = None) -> AddonInfos:
        log.info(f"Offline: {offline}")
        overrider: Overrider = Overrider(snapshot_dir)
        addon_page_parser: AddonPageParser = AddonPageParser(overrider)
        page_downloader: PageDownloader = PageDownloader(self.__page_load_timeout, self.__element_wait_timeout)
        addons_page_downloader: AddonsPageDownloader = AddonsPageDownloader(page_downloader, snapshot_dir, offline)
        addon_page_downloader: AddonPageDownloader = AddonPageDownloader(
            page_downloader, snapshot_dir, addon_page_parser, offline)
        ankiweb_service: AnkiWebService = AnkiWebService(addons_page_downloader, addon_page_downloader)
        github_rest_client: GithubRestClient = GithubRestClient(offline, self.__config.github.token_file)
        github_service: GithubService = GithubService(snapshot_dir, github_rest_client, prev_snapshot_dir, offline)
        discourse_client: DiscourseClient = DiscourseClient(host="https://forums.ankiweb.net",
                                                            api_username=None, api_key=None)
        anki_forum_service: AnkiForumService = AnkiForumService(discourse_client, snapshot_dir, offline)
        github_enricher: GithubEnricher = GithubEnricher(snapshot_dir, github_service)
        anki_forum_enricher: AnkiForumEnricher = AnkiForumEnricher(snapshot_dir, anki_forum_service)
        max_addons: Optional[int] = SampleCollector(snapshot_dir).effective_addons(
            self.__config.sample.addons) if offline else self.__config.sample.addons
        addon_infos_collector: AddonInfosCollector = AddonInfosCollector(
            ankiweb_service, github_enricher, anki_forum_enricher, max_addons)
        return addon_infos_collector.collect_addons()
