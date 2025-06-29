import tempfile
from datetime import date
from pathlib import Path
from textwrap import dedent

from anki_addons_dataset.huggingface.hugging_face import HuggingFace


def test_create_dataset_card():
    dataset_dir: Path = Path(tempfile.mkdtemp())
    exp_file: Path = dataset_dir / "README.md"
    assert not exp_file.exists()
    creation_date: date = date(2025, 1, 25)
    hugging_face: HuggingFace = HuggingFace(dataset_dir, creation_date)
    hugging_face.create_dataset_card()
    assert exp_file.exists()


def test_create_metadata_yaml():
    dataset_dir: Path = Path(tempfile.mkdtemp())
    exp_file: Path = dataset_dir / "metadata.json"
    assert not exp_file.exists()
    creation_date: date = date(2025, 1, 25)
    hugging_face: HuggingFace = HuggingFace(dataset_dir, creation_date)
    hugging_face.create_metadata_yaml()
    assert exp_file.read_text() == dedent(
        """\
        {
          "creation_date": "2025-01-25"
        }"""
    )
