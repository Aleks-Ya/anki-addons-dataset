import logging
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from unittest.mock import ANY, patch

import pandas
import pandas.testing as pdt
import pytest
from pandas import DataFrame

from anki_addons_dataset import __version__
from anki_addons_dataset.collector.ai.cache.ai_cache_stats import AiCacheStats
from anki_addons_dataset.collector.ai.provider.ai_provider import AiInstructions, AiPrompt, AiProvider, \
    AiResponseText
from anki_addons_dataset.collector.collector_facade import CollectorFacade
from anki_addons_dataset.collector.raw_metadata_collector import RawMetadataCollector
from anki_addons_dataset.collector.sample_collector import SampleCollector
from anki_addons_dataset.common.data_types import AddonInfos, ElementWaitTimeout, PageLoadTimeout, ReportDate, \
    ScriptVersion, SnapshotDate, AiModel, AddonPackage, AddonPackages, AddonReview, AnkiPointVersion, LanguageName, \
    ReviewVote
from anki_addons_dataset.common.json_helper import JsonHelper
from anki_addons_dataset.common.working_dir import SnapshotDir, WorkingDir
from anki_addons_dataset.config.app_config import AppConfig

# The string form, not patch.object: the name-mangled private attribute is unresolvable for static analysis.
__SUMMARIZE_SNAPSHOT: str = \
    "anki_addons_dataset.collector.collector_facade.CollectorFacade._CollectorFacade__summarize_snapshot"
__PARSE_SNAPSHOT: str = \
    "anki_addons_dataset.collector.collector_facade.CollectorFacade._CollectorFacade__parse_snapshot"
__COLLECT: str = \
    "anki_addons_dataset.collector.collector_facade.CollectorFacade._CollectorFacade__collect"
__REPORT_SNAPSHOT: str = \
    "anki_addons_dataset.collector.collector_facade.CollectorFacade._CollectorFacade__report_snapshot"
__PAGE_DOWNLOADER: str = "anki_addons_dataset.collector.collector_facade.PageDownloader"
__ADDON_INFOS_COLLECTOR: str = "anki_addons_dataset.collector.collector_facade.AddonInfosCollector"
__AI_PROVIDER_FACTORY: str = "anki_addons_dataset.collector.collector_facade.AiProviderFactory"


class AnsweringAiProvider(AiProvider):
    def __init__(self):
        super().__init__(AiModel("test-model"))

    def response(self, prompt: AiPrompt, instructions: Optional[AiInstructions] = None) -> Optional[AiResponseText]:
        return AiResponseText("statistics")

    def verify_access(self) -> Optional[str]:
        return None


def test_download_snapshot_collects_packages_of_scraped_addons(
        collector_facade: CollectorFacade, snapshot_dir: SnapshotDir, snapshot_date: SnapshotDate,
        addon_infos: AddonInfos):
    with patch(__COLLECT, return_value=addon_infos), \
            patch("anki_addons_dataset.collector.collector_facade.AnkiVersionsCollector"), \
            patch("anki_addons_dataset.collector.collector_facade.PackageCollector") as package_collector:
        collector_facade.download_snapshot(snapshot_date)

    package_collector.return_value.collect.assert_called_once_with(addon_infos)
    assert package_collector.call_args.args[0] == snapshot_dir


def test_report_snapshots_exports_packages(
        collector_facade: CollectorFacade, snapshot_dir: SnapshotDir, addon_infos: AddonInfos,
        script_version: ScriptVersion, report_date: ReportDate):
    addon_infos = AddonInfos([replace(addon_infos[0], package=AddonPackages([AddonPackage(
        "45-2026-01-15-0123456789ab.ankiaddon", AnkiPointVersion(45), date(2026, 1, 15), 10, None, None,
        1, 6, 1, 1, ["__init__.py"], {LanguageName("python"): 6})]))])
    JsonHelper.write_addon_infos_dump(addon_infos, script_version, snapshot_dir.get_addon_infos_dump())

    collector_facade.report_snapshots(None, report_date)

    packages_df: DataFrame = pandas.read_parquet(snapshot_dir.get_final_dir() / "parquet" / "packages.parquet")
    assert list(packages_df["addon_id"]) == [addon_infos[0].header.id]
    assert list(packages_df["file_name"]) == ["45-2026-01-15-0123456789ab.ankiaddon"]
    assert list(packages_df["language_bytes"][0]) == [{"name": "python", "bytes": 6}]
    data_df: DataFrame = pandas.read_parquet(snapshot_dir.get_final_dir() / "parquet" / "data.parquet")
    assert data_df.iloc[0]["package"]["file_name"] == "45-2026-01-15-0123456789ab.ankiaddon"
    assert data_df.iloc[0]["package"]["primary_language"] == "python"


def test_report_snapshots_generates_final_from_dump_without_raw(
        collector_facade: CollectorFacade, snapshot_dir: SnapshotDir, addon_infos: AddonInfos,
        script_version: ScriptVersion, report_date: ReportDate):
    # A 2-stage artifact that REPORT must not touch, and no 1-raw at all — proves decoupling from raw.
    stage_marker = snapshot_dir.get_stage_dir() / "marker.txt"
    stage_marker.write_text("keep me")
    JsonHelper.write_addon_infos_dump(addon_infos, script_version, snapshot_dir.get_addon_infos_dump())

    collector_facade.report_snapshots(None, report_date)

    final_dir = snapshot_dir.get_final_dir()
    assert (final_dir / "parquet" / "data.parquet").exists()
    assert (final_dir / "parquet" / "tags.parquet").exists()
    assert (final_dir / "xlsx" / "tags.xlsx").exists()
    assert not (final_dir / "json").exists()
    assert snapshot_dir.get_metadata_json().exists()
    assert stage_marker.exists()
    assert not snapshot_dir.get_raw_dir().joinpath("1-anki-web").exists()


def test_report_snapshots_exports_anki_versions(
        collector_facade: CollectorFacade, snapshot_dir: SnapshotDir, addon_infos: AddonInfos,
        script_version: ScriptVersion, report_date: ReportDate):
    JsonHelper.write_addon_infos_dump(addon_infos, script_version, snapshot_dir.get_addon_infos_dump())
    tags_file: Path = snapshot_dir.get_raw_dir() / "2-github" / "ankitects" / "anki" / "tags.json"
    tags_file.parent.mkdir(parents=True)
    tags_file.write_text('[{"ref": "refs/tags/2.1.66"}, {"ref": "refs/tags/25.09.2"}]')
    tags_file.with_name("releases.json").write_text('[{"tag_name": "25.09.2", "published_at": "2025-10-01T12:30:00Z"}]')

    collector_facade.report_snapshots(None, report_date)

    final_dir = snapshot_dir.get_final_dir()
    pdt.assert_frame_equal(pandas.read_parquet(final_dir / "parquet" / "anki_versions.parquet"), DataFrame([
        {"version": "25.09.2", "point_version": 250902, "release_date": date(2025, 10, 1)},
        {"version": "2.1.66", "point_version": 66, "release_date": None}]))
    assert (final_dir / "xlsx" / "anki_versions.xlsx").exists()


def test_report_snapshots_exports_reviews_newest_first(
        collector_facade: CollectorFacade, snapshot_dir: SnapshotDir, addon_infos: AddonInfos,
        script_version: ScriptVersion, report_date: ReportDate):
    addon_infos = AddonInfos([replace(addon_infos[0], page=replace(addon_infos[0].page, reviews=[
        AddonReview(ReviewVote.LIKE, date(2025, 6, 6), "Works", "Thank you!"),
        AddonReview(ReviewVote.DISLIKE, date(2026, 7, 5), "Produces errors")]))])
    JsonHelper.write_addon_infos_dump(addon_infos, script_version, snapshot_dir.get_addon_infos_dump())

    collector_facade.report_snapshots(None, report_date)

    final_dir = snapshot_dir.get_final_dir()
    addon_id: int = addon_infos[0].header.id
    pdt.assert_frame_equal(pandas.read_parquet(final_dir / "parquet" / "reviews.parquet"), DataFrame([
        {"addon_id": addon_id, "date": date(2026, 7, 5), "vote": "dislike", "text": "Produces errors",
         "author_reply": None},
        {"addon_id": addon_id, "date": date(2025, 6, 6), "vote": "like", "text": "Works",
         "author_reply": "Thank you!"}]))
    assert not (final_dir / "xlsx" / "reviews.xlsx").exists()


def test_report_snapshots_without_anki_tags_skips_anki_versions(
        collector_facade: CollectorFacade, snapshot_dir: SnapshotDir, addon_infos: AddonInfos,
        script_version: ScriptVersion, report_date: ReportDate, caplog: pytest.LogCaptureFixture):
    JsonHelper.write_addon_infos_dump(addon_infos, script_version, snapshot_dir.get_addon_infos_dump())

    with caplog.at_level(logging.WARNING):
        collector_facade.report_snapshots(None, report_date)

    final_dir = snapshot_dir.get_final_dir()
    assert (final_dir / "parquet" / "tags.parquet").exists()
    assert not (final_dir / "parquet" / "anki_versions.parquet").exists()
    assert not (final_dir / "xlsx" / "anki_versions.xlsx").exists()
    assert "the anki_versions table is skipped" in caplog.text


def test_report_snapshots_missing_dump_raises(
        collector_facade: CollectorFacade, snapshot_dir: SnapshotDir, report_date: ReportDate):
    with pytest.raises(FileNotFoundError, match="Run the 'parse' operation first"):
        collector_facade.report_snapshots(None, report_date)


def test_report_snapshots_no_snapshots_is_noop(collector_facade: CollectorFacade, report_date: ReportDate):
    collector_facade.report_snapshots(None, report_date)  # must not raise when history is empty


def test_summarize_snapshots_no_snapshots_is_noop(collector_facade: CollectorFacade,
                                                 caplog: pytest.LogCaptureFixture):
    with caplog.at_level(logging.INFO):
        # must not raise, and must not read the AI key, when history is empty
        collector_facade.summarize_snapshots(None)

    assert "Total AI cache hits: 0, misses: 0" in caplog.text


def test_summarize_snapshots_totals_the_cache_stats_of_all_snapshots(
        working_dir: WorkingDir, collector_facade: CollectorFacade, caplog: pytest.LogCaptureFixture):
    for snapshot_date in ["2025-01-01", "2025-02-01"]:
        working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat(snapshot_date))).create()
    stats: list[AiCacheStats] = [AiCacheStats(hit_count=7, miss_count=1), AiCacheStats(hit_count=2, miss_count=3)]

    # The per-snapshot summarizing itself needs a full 1-raw snapshot, and is not what this test is about.
    with patch(__SUMMARIZE_SNAPSHOT, side_effect=stats):
        with caplog.at_level(logging.INFO):
            collector_facade.summarize_snapshots(None)

    assert "Total AI cache hits: 9, misses: 4" in caplog.text


def test_summarize_snapshots_with_a_date_summarizes_only_that_snapshot(
        working_dir: WorkingDir, collector_facade: CollectorFacade):
    snapshot_dirs: list[SnapshotDir] = [
        working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat(snapshot_date))).create()
        for snapshot_date in ["2025-01-01", "2025-02-01"]]

    with patch(__SUMMARIZE_SNAPSHOT, return_value=AiCacheStats()) as summarize_snapshot:
        collector_facade.summarize_snapshots(SnapshotDate(date.fromisoformat("2025-01-01")))

    assert summarize_snapshot.call_count == 1
    assert summarize_snapshot.call_args.args[0] == snapshot_dirs[0]


def test_summarize_snapshots_with_a_date_wins_over_the_snapshot_sample(
        working_dir_path: Path, app_config: AppConfig, page_load_timeout: PageLoadTimeout,
        element_wait_timeout: ElementWaitTimeout):
    working_dir: WorkingDir = WorkingDir(working_dir_path, max_snapshots=1)
    old_dir: SnapshotDir = working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat("2025-01-01"))).create()
    working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat("2025-02-01"))).create()
    collector_facade: CollectorFacade = CollectorFacade(
        working_dir, app_config, page_load_timeout, element_wait_timeout)

    with patch(__SUMMARIZE_SNAPSHOT, return_value=AiCacheStats()) as summarize_snapshot:
        collector_facade.summarize_snapshots(SnapshotDate(date.fromisoformat("2025-01-01")))

    assert summarize_snapshot.call_count == 1
    assert summarize_snapshot.call_args.args[0] == old_dir


def test_summarize_snapshots_with_an_unknown_date_raises(collector_facade: CollectorFacade):
    unknown_date: SnapshotDate = SnapshotDate(date.fromisoformat("1999-01-01"))

    with pytest.raises(FileNotFoundError, match="No snapshot for 1999-01-01"):
        collector_facade.summarize_snapshots(unknown_date)


def test_parse_snapshots_with_a_date_parses_only_that_snapshot(
        working_dir: WorkingDir, collector_facade: CollectorFacade):
    for snapshot_date in ["2025-01-01", "2025-02-01"]:
        working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat(snapshot_date))).create()

    with patch(__PARSE_SNAPSHOT) as parse_snapshot:
        collector_facade.parse_snapshots(SnapshotDate(date.fromisoformat("2025-01-01")))

    parse_snapshot.assert_called_once_with(SnapshotDate(date.fromisoformat("2025-01-01")), ANY)


def test_parse_snapshots_with_a_date_wins_over_the_snapshot_sample(
        working_dir_path: Path, app_config: AppConfig, page_load_timeout: PageLoadTimeout,
        element_wait_timeout: ElementWaitTimeout):
    working_dir: WorkingDir = WorkingDir(working_dir_path, max_snapshots=1)
    for snapshot_date in ["2025-01-01", "2025-02-01"]:
        working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat(snapshot_date))).create()
    collector_facade: CollectorFacade = CollectorFacade(
        working_dir, app_config, page_load_timeout, element_wait_timeout)

    with patch(__PARSE_SNAPSHOT) as parse_snapshot:
        collector_facade.parse_snapshots(SnapshotDate(date.fromisoformat("2025-01-01")))

    parse_snapshot.assert_called_once_with(SnapshotDate(date.fromisoformat("2025-01-01")), ANY)


def test_parse_snapshots_with_an_unknown_date_raises(collector_facade: CollectorFacade):
    unknown_date: SnapshotDate = SnapshotDate(date.fromisoformat("1999-01-01"))

    with pytest.raises(FileNotFoundError, match="No snapshot for 1999-01-01"):
        collector_facade.parse_snapshots(unknown_date)


def test_report_snapshots_honours_the_snapshot_sample(
        working_dir_path: Path, app_config: AppConfig, page_load_timeout: PageLoadTimeout,
        element_wait_timeout: ElementWaitTimeout, addon_infos: AddonInfos, script_version: ScriptVersion,
        report_date: ReportDate):
    working_dir: WorkingDir = WorkingDir(working_dir_path, max_snapshots=1)
    old_dir: SnapshotDir = working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat("2025-01-01"))).create()
    new_dir: SnapshotDir = working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat("2025-02-01"))).create()
    for snapshot_dir in [old_dir, new_dir]:
        JsonHelper.write_addon_infos_dump(addon_infos, script_version, snapshot_dir.get_addon_infos_dump())

    CollectorFacade(working_dir, app_config, page_load_timeout, element_wait_timeout).report_snapshots(
        None, report_date)

    assert (new_dir.get_final_dir() / "parquet" / "data.parquet").exists()
    assert not (old_dir.get_final_dir() / "parquet" / "data.parquet").exists()


def test_report_snapshots_with_a_date_reports_only_that_snapshot(
        working_dir: WorkingDir, collector_facade: CollectorFacade, report_date: ReportDate):
    for snapshot_date in ["2025-01-01", "2025-02-01"]:
        working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat(snapshot_date))).create()

    with patch(__REPORT_SNAPSHOT) as report_snapshot:
        collector_facade.report_snapshots(SnapshotDate(date.fromisoformat("2025-01-01")), report_date)

    report_snapshot.assert_called_once_with(SnapshotDate(date.fromisoformat("2025-01-01")), report_date)


def test_report_snapshots_with_a_date_wins_over_the_snapshot_sample(
        working_dir_path: Path, app_config: AppConfig, page_load_timeout: PageLoadTimeout,
        element_wait_timeout: ElementWaitTimeout, report_date: ReportDate):
    working_dir: WorkingDir = WorkingDir(working_dir_path, max_snapshots=1)
    for snapshot_date in ["2025-01-01", "2025-02-01"]:
        working_dir.get_snapshot_dir(SnapshotDate(date.fromisoformat(snapshot_date))).create()
    collector_facade: CollectorFacade = CollectorFacade(
        working_dir, app_config, page_load_timeout, element_wait_timeout)

    with patch(__REPORT_SNAPSHOT) as report_snapshot:
        collector_facade.report_snapshots(SnapshotDate(date.fromisoformat("2025-01-01")), report_date)

    report_snapshot.assert_called_once_with(SnapshotDate(date.fromisoformat("2025-01-01")), report_date)


def test_report_snapshots_with_an_unknown_date_raises(collector_facade: CollectorFacade, report_date: ReportDate):
    unknown_date: SnapshotDate = SnapshotDate(date.fromisoformat("1999-01-01"))

    with pytest.raises(FileNotFoundError, match="No snapshot for 1999-01-01"):
        collector_facade.report_snapshots(unknown_date, report_date)


def test_download_snapshot_without_a_date_raises(collector_facade: CollectorFacade):
    with pytest.raises(ValueError, match="Snapshot date is required"):
        collector_facade.download_snapshot(None)


def test_download_snapshot_resumed_keeps_the_recorded_timestamps(
        collector_facade: CollectorFacade, snapshot_dir: SnapshotDir, snapshot_date: SnapshotDate,
        addon_infos: AddonInfos):
    raw_metadata_collector: RawMetadataCollector = RawMetadataCollector(snapshot_dir)
    raw_metadata_collector.set_start_datetime(datetime(2025, 1, 1, 10, 0, 0))
    raw_metadata_collector.set_finish_datetime(datetime(2025, 1, 1, 12, 0, 0))

    with patch(__COLLECT, return_value=addon_infos), \
            patch("anki_addons_dataset.collector.collector_facade.AnkiVersionsCollector"), \
            patch("anki_addons_dataset.collector.collector_facade.PackageCollector"):
        collector_facade.download_snapshot(snapshot_date)

    raw_metadata = raw_metadata_collector.read_metadata()
    assert raw_metadata.start_timestamp == datetime(2025, 1, 1, 10, 0, 0)
    assert raw_metadata.finish_timestamp == datetime(2025, 1, 1, 12, 0, 0)


def test_report_snapshots_of_a_current_dump_does_not_warn(
        collector_facade: CollectorFacade, snapshot_dir: SnapshotDir, addon_infos: AddonInfos,
        report_date: ReportDate, caplog: pytest.LogCaptureFixture):
    JsonHelper.write_addon_infos_dump(addon_infos, ScriptVersion(__version__), snapshot_dir.get_addon_infos_dump())

    with caplog.at_level(logging.WARNING):
        collector_facade.report_snapshots(None, report_date)

    assert (snapshot_dir.get_final_dir() / "parquet" / "data.parquet").exists()
    assert "Dump was parsed with script version" not in caplog.text


@pytest.mark.parametrize("fork_verify_model", [None, "verify-model"])
def test_parse_snapshots_writes_the_dump_and_warns_about_missing_ai_answers(
        working_dir: WorkingDir, app_config: AppConfig, page_load_timeout: PageLoadTimeout,
        element_wait_timeout: ElementWaitTimeout, snapshot_dir: SnapshotDir, addon_infos: AddonInfos,
        caplog: pytest.LogCaptureFixture, fork_verify_model: Optional[str]):
    config: AppConfig = replace(app_config, ai=replace(app_config.ai, fork_verify_model=fork_verify_model))
    SampleCollector(snapshot_dir).set_addons(3)
    collector_facade: CollectorFacade = CollectorFacade(working_dir, config, page_load_timeout, element_wait_timeout)

    with patch(__PAGE_DOWNLOADER), patch(__ADDON_INFOS_COLLECTOR) as addon_infos_collector:
        addon_infos_collector.return_value.collect_addons.return_value = addon_infos
        with caplog.at_level(logging.WARNING):
            collector_facade.parse_snapshots(None)

    _, dumped_addon_infos = JsonHelper.read_addon_infos_dump(snapshot_dir.get_addon_infos_dump())
    assert [addon_info.header.id for addon_info in dumped_addon_infos] == [
        addon_info.header.id for addon_info in addon_infos]
    assert "AI answers (repo choices, forum topic checks, summaries, tags or fork labels) are missing" in caplog.text
    assert addon_infos_collector.call_args.args[5] == 3


def test_summarize_snapshots_fills_the_ai_cache_and_keeps_the_report(
        collector_facade: CollectorFacade, snapshot_dir: SnapshotDir, addon_infos: AddonInfos,
        caplog: pytest.LogCaptureFixture):
    report_file: Path = snapshot_dir.get_final_dir() / "parquet" / "data.parquet"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text("existing report")

    with patch(__PAGE_DOWNLOADER), patch(__ADDON_INFOS_COLLECTOR) as addon_infos_collector, \
            patch(__AI_PROVIDER_FACTORY) as ai_provider_factory:
        addon_infos_collector.return_value.collect_addons.return_value = addon_infos
        ai_provider_factory.create.return_value = AnsweringAiProvider()
        with caplog.at_level(logging.INFO):
            collector_facade.summarize_snapshots(None)

    assert snapshot_dir.get_ai_cache_file().read_text().strip()
    assert report_file.read_text() == "existing report"
    assert "AI cache hits: 0, misses: " in caplog.text
    ai_provider_factory.create.assert_called_once_with(ANY, False, None)


def test_parse_snapshots_reads_back_the_answers_the_ai_step_cached(
        collector_facade: CollectorFacade, snapshot_dir: SnapshotDir, addon_infos: AddonInfos,
        caplog: pytest.LogCaptureFixture):
    with patch(__PAGE_DOWNLOADER), patch(__ADDON_INFOS_COLLECTOR) as addon_infos_collector, \
            patch(__AI_PROVIDER_FACTORY) as ai_provider_factory:
        addon_infos_collector.return_value.collect_addons.return_value = addon_infos
        ai_provider_factory.create.return_value = AnsweringAiProvider()
        collector_facade.summarize_snapshots(None)
        with caplog.at_level(logging.WARNING):
            collector_facade.parse_snapshots(None)

    _, dumped_addon_infos = JsonHelper.read_addon_infos_dump(snapshot_dir.get_addon_infos_dump())
    assert [addon_info.ai.summary for addon_info in dumped_addon_infos if addon_info.ai] == ["statistics"]
    assert "are missing from the cache" not in caplog.text
