import tempfile
from pathlib import Path

from pytest import fixture

from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonId
from anki_addons_dataset.common.working_dir import WorkingDir


@fixture
def working_dir_path() -> Path:
    return Path(tempfile.mkdtemp())


@fixture
def working_dir(working_dir_path: Path) -> WorkingDir:
    return WorkingDir(working_dir_path)


@fixture
def overrider(working_dir: WorkingDir) -> Overrider:
    return Overrider(working_dir.get_dataset_dir())


@fixture
def note_size_addon_id() -> AddonId:
    return AddonId(1188705668)


@fixture
def hyper_tts_addon_id() -> AddonId:
    return AddonId(111623432)
