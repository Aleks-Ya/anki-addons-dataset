import tempfile
from pathlib import Path

from anki_addons_dataset.huggingface.hugging_face import HuggingFace


def test_create_dataset_card():
    bundle_dir: Path = Path(tempfile.mkdtemp())
    exp_file: Path = bundle_dir / "README.md"
    assert not exp_file.exists()
    HuggingFace.create_dataset_card(bundle_dir)
    assert exp_file.exists()
