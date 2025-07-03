import tempfile
from datetime import date
from pathlib import Path

from pytest import fixture

from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonId
from anki_addons_dataset.common.working_dir import WorkingDir, VersionDir


@fixture
def working_dir_path() -> Path:
    return Path(tempfile.mkdtemp())


@fixture
def working_dir(working_dir_path: Path) -> WorkingDir:
    return WorkingDir(working_dir_path)


@fixture
def version_dir(working_dir: WorkingDir) -> VersionDir:
    return working_dir.get_version_dir(date.fromisoformat("2025-01-25"))


@fixture
def overrider(version_dir: VersionDir) -> Overrider:
    return Overrider(version_dir)


@fixture
def note_size_addon_id() -> AddonId:
    return AddonId(1188705668)


@fixture
def hyper_tts_addon_id() -> AddonId:
    return AddonId(111623432)
