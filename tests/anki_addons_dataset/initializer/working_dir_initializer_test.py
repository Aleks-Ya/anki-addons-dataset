import json
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

import pytest
from freezegun import freeze_time
from seedir import seedir

from anki_addons_dataset.common.log import Log
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient
from anki_addons_dataset.initializer.working_dir_initializer import WorkingDirInitializer


def test_initialize_working_dir(working_dir: WorkingDir, working_dir_initializer: WorkingDirInitializer,
                                hugging_face_client: HuggingFaceClient):
    working_dir.get_path().rmdir()
    assert not working_dir.get_path().exists()

    raw_zip: Path = Path(tempfile.mkstemp(".zip")[1])
    exp_metadata: str = "abc"
    with ZipFile(raw_zip, "w") as zw:
        zw.writestr("raw-metadata.json", exp_metadata)

    hugging_face_client.list_snapshot_folders = Mock(return_value=["history/2025-01-01"])
    hugging_face_client.download_file = Mock(return_value=raw_zip)

    working_dir_initializer.initialize_working_dir()

    tree: str = seedir(working_dir.get_path(), printout=False, sort=True)
    assert tree == textwrap.dedent(f"""\
                                    {working_dir.get_path().name}/
                                    └─history/
                                      └─2025-01-01/
                                        ├─1-raw/
                                        │ └─raw-metadata.json
                                        ├─2-stage/
                                        └─3-final/""")
    act_metadata_file: Path = working_dir.get_history_dir() / '2025-01-01' / '1-raw' / 'raw-metadata.json'
    assert act_metadata_file.read_text() == exp_metadata


def __raw_zip(package_list: list[str]) -> Path:
    raw_zip: Path = Path(tempfile.mkstemp(".zip")[1])
    with ZipFile(raw_zip, "w") as zw:
        zw.writestr("package-list.json", json.dumps(package_list))
    return raw_zip


def test_initialize_working_dir_restores_listed_packages(working_dir: WorkingDir,
                                                         working_dir_initializer: WorkingDirInitializer,
                                                         hugging_face_client: HuggingFaceClient, tmp_path: Path):
    entry: str = "100/45-2026-01-15-0123456789ab.ankiaddon"
    hf_package: Path = tmp_path / "packages" / entry
    hf_package.parent.mkdir(parents=True)
    hf_package.write_text("package")
    hugging_face_client.list_snapshot_folders = Mock(return_value=["history/2026-02-01", "history/2026-03-01"])
    hugging_face_client.download_file = Mock(return_value=__raw_zip([entry]))
    hugging_face_client.download_packages = Mock(return_value=tmp_path)

    working_dir_initializer.initialize_working_dir()

    hugging_face_client.download_packages.assert_called_once()
    for day in ["2026-02-01", "2026-03-01"]:
        restored: Path = working_dir.get_history_dir() / day / "1-raw" / "5-package" / entry
        assert restored.read_text() == "package"


def test_initialize_working_dir_skips_snapshots_without_package_list(working_dir_initializer: WorkingDirInitializer,
                                                                     hugging_face_client: HuggingFaceClient):
    raw_zip: Path = Path(tempfile.mkstemp(".zip")[1])
    with ZipFile(raw_zip, "w") as zw:
        zw.writestr("raw-metadata.json", "abc")
    hugging_face_client.list_snapshot_folders = Mock(return_value=["history/2025-01-01"])
    hugging_face_client.download_file = Mock(return_value=raw_zip)
    hugging_face_client.download_packages = Mock()

    working_dir_initializer.initialize_working_dir()

    hugging_face_client.download_packages.assert_not_called()


def test_initialize_working_dir_warns_about_package_missing_from_hf(working_dir: WorkingDir,
                                                                    working_dir_initializer: WorkingDirInitializer,
                                                                    hugging_face_client: HuggingFaceClient,
                                                                    tmp_path: Path,
                                                                    caplog: pytest.LogCaptureFixture):
    entry: str = "100/45-2026-01-15-0123456789ab.ankiaddon"
    hugging_face_client.list_snapshot_folders = Mock(return_value=["history/2026-02-01"])
    hugging_face_client.download_file = Mock(return_value=__raw_zip([entry]))
    hugging_face_client.download_packages = Mock(return_value=tmp_path)

    working_dir_initializer.initialize_working_dir()

    assert entry in caplog.text
    assert not (working_dir.get_history_dir() / "2026-02-01" / "1-raw" / "5-package" / entry).exists()


@freeze_time("2026-05-01 14:25:45")
def test_initialize_working_dir_backs_up_existing_content(working_dir: WorkingDir,
                                                          working_dir_initializer: WorkingDirInitializer,
                                                          hugging_face_client: HuggingFaceClient,
                                                          monkeypatch: pytest.MonkeyPatch):
    (working_dir.get_history_dir() / "2024-01-01").mkdir(parents=True)
    log_file: Path = working_dir.get_path() / "logs" / "anki-addons-dataset-2026-05-01-142545.log"
    log_file.parent.mkdir(parents=True)
    log_file.write_text("current run")
    monkeypatch.setattr(Log, "active_log_file", staticmethod(lambda: log_file))

    raw_zip: Path = Path(tempfile.mkstemp(".zip")[1])
    with ZipFile(raw_zip, "w") as zw:
        zw.writestr("raw-metadata.json", "abc")

    hugging_face_client.list_snapshot_folders = Mock(return_value=["history/2025-01-01"])
    hugging_face_client.download_file = Mock(return_value=raw_zip)

    working_dir_initializer.initialize_working_dir()

    assert (working_dir.get_backups_dir() / "20260501-142545" / "history" / "2024-01-01").is_dir()
    assert (working_dir.get_history_dir() / "2025-01-01" / "1-raw" / "raw-metadata.json").is_file()
    assert not (working_dir.get_history_dir() / "2024-01-01").exists()
    assert log_file.read_text() == "current run"
