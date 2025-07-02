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
def dataset_path(working_dir_path: Path) -> Path:
    return working_dir_path / "dataset"


@fixture
def working_dir(working_dir_path: Path) -> WorkingDir:
    return WorkingDir(working_dir_path)


@fixture
def overrider(dataset_path: Path) -> Overrider:
    return Overrider(dataset_path)


@fixture
def note_size_addon_id() -> AddonId:
    return AddonId(1188705668)


@fixture
def hyper_tts_addon_id() -> AddonId:
    return AddonId(111623432)
