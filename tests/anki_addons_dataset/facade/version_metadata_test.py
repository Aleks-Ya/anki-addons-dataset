from datetime import date, datetime
from pathlib import Path
from textwrap import dedent

from anki_addons_dataset.common.working_dir import WorkingDir, VersionDir
from anki_addons_dataset.facade.version_metadata import VersionMetadata


def test_set_start_datetime(working_dir: WorkingDir):
    version_dir: VersionDir = working_dir.get_version_dir(date.fromisoformat("2025-01-01")).create()
    version_metadata: VersionMetadata = VersionMetadata(version_dir)
    assert version_metadata.get_start_datetime() is None
    assert version_metadata.get_finish_datetime() is None
    assert version_metadata.get_script_version() is None
    start_datetime: datetime = datetime.fromisoformat("2025-01-02T15:45:50")
    version_metadata.set_start_datetime(start_datetime)
    assert version_metadata.get_start_datetime() == start_datetime
    assert version_metadata.get_finish_datetime() is None
    assert version_metadata.get_script_version() is None


def test_set_finish_datetime(working_dir: WorkingDir):
    version_dir: VersionDir = working_dir.get_version_dir(date.fromisoformat("2025-01-01")).create()
    version_metadata: VersionMetadata = VersionMetadata(version_dir)
    assert version_metadata.get_start_datetime() is None
    assert version_metadata.get_finish_datetime() is None
    assert version_metadata.get_script_version() is None
    start_datetime: datetime = datetime.fromisoformat("2025-01-02T15:45:50")
    finish_datetime: datetime = datetime.fromisoformat("2025-01-03T16:46:51")
    version_metadata.set_start_datetime(start_datetime)
    version_metadata.set_finish_datetime(finish_datetime)
    assert version_metadata.get_start_datetime() == start_datetime
    assert version_metadata.get_finish_datetime() == finish_datetime
    assert version_metadata.get_script_version() is None


def test_set_script_version(working_dir: WorkingDir):
    version_dir: VersionDir = working_dir.get_version_dir(date.fromisoformat("2025-01-01")).create()
    version_metadata: VersionMetadata = VersionMetadata(version_dir)
    assert version_metadata.get_start_datetime() is None
    assert version_metadata.get_finish_datetime() is None
    assert version_metadata.get_script_version() is None
    script_version: str = "v0.0.1"
    version_metadata.set_script_version(script_version)
    assert version_metadata.get_start_datetime() is None
    assert version_metadata.get_finish_datetime() is None
    assert version_metadata.get_script_version() == script_version


def test_file_content(working_dir: WorkingDir):
    version_dir: VersionDir = working_dir.get_version_dir(date.fromisoformat("2025-01-01")).create()
    metadata_file: Path = version_dir.get_raw_dir() / "raw-metadata.json"
    assert not metadata_file.exists()
    version_metadata: VersionMetadata = VersionMetadata(version_dir)
    script_version: str = "v0.0.1"
    start_datetime: datetime = datetime.fromisoformat("2025-01-02T15:45:50.385843")
    finish_datetime: datetime = datetime.fromisoformat("2025-01-03T16:46:51")
    version_metadata.set_start_datetime(start_datetime)
    version_metadata.set_finish_datetime(finish_datetime)
    version_metadata.set_script_version(script_version)
    assert metadata_file.exists()
    assert metadata_file.read_text() == dedent("""\
    {
      "start_timestamp": "2025-01-02T15:45:50.385843",
      "finish_timestamp": "2025-01-03T16:46:51",
      "script_version": "v0.0.1"
    }""")
