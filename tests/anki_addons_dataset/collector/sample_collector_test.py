import json

import pytest
from _pytest.logging import LogCaptureFixture

from anki_addons_dataset.collector.sample_collector import SampleCollector
from anki_addons_dataset.common.working_dir import SnapshotDir


def test_no_sample_file_means_no_limit(snapshot_dir: SnapshotDir):
    sample_collector: SampleCollector = SampleCollector(snapshot_dir)
    assert sample_collector.read_addons() is None
    assert sample_collector.effective_addons(None) is None
    assert sample_collector.effective_addons(5) == 5


def test_round_trip(snapshot_dir: SnapshotDir):
    sample_collector: SampleCollector = SampleCollector(snapshot_dir)
    sample_collector.set_addons(20)
    assert json.loads(snapshot_dir.get_sample_file().read_text()) == {"addons": 20}
    assert sample_collector.read_addons() == 20


def test_an_unsampled_download_records_no_limit(snapshot_dir: SnapshotDir):
    sample_collector: SampleCollector = SampleCollector(snapshot_dir)
    sample_collector.set_addons(None)
    assert sample_collector.read_addons() is None
    assert sample_collector.effective_addons(None) is None


def test_the_recorded_limit_applies_without_the_flag(snapshot_dir: SnapshotDir):
    SampleCollector(snapshot_dir).set_addons(20)
    assert SampleCollector(snapshot_dir).effective_addons(None) == 20


@pytest.mark.parametrize("configured, expected", [(5, 5), (50, 20)])
def test_the_smaller_limit_wins(snapshot_dir: SnapshotDir, caplog: LogCaptureFixture,
                                configured: int, expected: int):
    SampleCollector(snapshot_dir).set_addons(20)
    assert SampleCollector(snapshot_dir).effective_addons(configured) == expected
    assert "was downloaded" in caplog.text


def test_a_matching_limit_is_not_warned_about(snapshot_dir: SnapshotDir, caplog: LogCaptureFixture):
    SampleCollector(snapshot_dir).set_addons(20)
    assert SampleCollector(snapshot_dir).effective_addons(20) == 20
    assert "using" not in caplog.text
