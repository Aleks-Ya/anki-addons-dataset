import logging
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pandas
import pandas.testing as pdt
import pytest
from pandas import DataFrame

from anki_addons_dataset.collector.ai.ai_cache_stats import AiCacheStats
from anki_addons_dataset.collector.collector_facade import CollectorFacade
from anki_addons_dataset.common.data_types import AddonInfos, ElementWaitTimeout, PageLoadTimeout, ReportDate, \
    ScriptVersion, SnapshotDate, AddonReview, ReviewVote
from anki_addons_dataset.common.json_helper import JsonHelper
from anki_addons_dataset.common.working_dir import SnapshotDir, WorkingDir
from anki_addons_dataset.config.app_config import AppConfig

# The string form, not patch.object: the name-mangled private attribute is unresolvable for static analysis.
__SUMMARIZE_SNAPSHOT: str = \
    "anki_addons_dataset.collector.collector_facade.CollectorFacade._CollectorFacade__summarize_snapshot"
__PARSE_SNAPSHOT: str = \
    "anki_addons_dataset.collector.collector_facade.CollectorFacade._CollectorFacade__parse_snapshot"
__REPORT_SNAPSHOT: str = \
    "anki_addons_dataset.collector.collector_facade.CollectorFacade._CollectorFacade__report_snapshot"


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

    collector_facade.report_snapshots(None, report_date)

    final_dir = snapshot_dir.get_final_dir()
    pdt.assert_frame_equal(pandas.read_parquet(final_dir / "parquet" / "anki_versions.parquet"), DataFrame([
        {"version": "25.09.2", "point_version": 250902}, {"version": "2.1.66", "point_version": 66}]))
    assert (final_dir / "xlsx" / "anki_versions.xlsx").exists()


def test_report_snapshots_exports_reviews_newest_first(
        collector_facade: CollectorFacade, snapshot_dir: SnapshotDir, addon_infos: AddonInfos,
        script_version: ScriptVersion, report_date: ReportDate):
    addon_infos[0].page.reviews = [AddonReview(ReviewVote.LIKE, date(2025, 6, 6), "Works", "Thank you!"),
                                   AddonReview(ReviewVote.DISLIKE, date(2026, 7, 5), "Produces errors")]
    JsonHelper.write_addon_infos_dump(addon_infos, script_version, snapshot_dir.get_addon_infos_dump())

    collector_facade.report_snapshots(None, report_date)

    final_dir = snapshot_dir.get_final_dir()
    addon_id: int = addon_infos[0].header.id
    pdt.assert_frame_equal(pandas.read_parquet(final_dir / "parquet" / "reviews.parquet"), DataFrame([
        {"addon_id": addon_id, "date": date(2026, 7, 5), "vote": "dislike", "text": "Produces errors",
         "author_reply": None},
        {"addon_id": addon_id, "date": date(2025, 6, 6), "vote": "like", "text": "Works", "author_reply": "Thank you!"}]))
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

    parse_snapshot.assert_called_once_with(SnapshotDate(date.fromisoformat("2025-01-01")))


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

    parse_snapshot.assert_called_once_with(SnapshotDate(date.fromisoformat("2025-01-01")))


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

    CollectorFacade(working_dir, app_config, page_load_timeout, element_wait_timeout).report_snapshots(None, report_date)

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
