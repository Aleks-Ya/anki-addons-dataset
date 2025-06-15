import tempfile
from pathlib import Path

from pytest import fixture

from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonId


@fixture
def dataset_path() -> Path:
    return Path(tempfile.mkdtemp())


@fixture
def overrider(dataset_path: Path) -> Overrider:
    return Overrider(dataset_path)


@fixture
def note_size_addon_id() -> AddonId:
    return AddonId(1188705668)


@fixture
def hyper_tts_addon_id() -> AddonId:
    return AddonId(111623432)
