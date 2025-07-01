import tempfile
from pathlib import Path
from textwrap import dedent

from anki_addons_dataset.huggingface.hugging_face import HuggingFace


def test_create_dataset_card():
    dataset_dir: Path = Path(tempfile.mkdtemp())
    exp_file: Path = dataset_dir / "README.md"
    assert not exp_file.exists()
    HuggingFace.create_dataset_card(dataset_dir)
    assert exp_file.exists()


def test_create_version_metadata_yaml():
    version_dir: Path = Path(tempfile.mkdtemp()) / "2025-01-25"
    exp_file: Path = version_dir / "metadata.json"
    assert not exp_file.exists()
    HuggingFace.create_version_metadata_yaml(version_dir)
    assert exp_file.read_text() == dedent(
        """\
        {
          "creation_date": "2025-01-25"
        }"""
    )
