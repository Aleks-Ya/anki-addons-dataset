from datetime import date

from anki_addons_dataset.common.data_types import HuggingFaceFolder
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient


def test_verify_write_access(hugging_face_client: HuggingFaceClient) -> None:
    hugging_face_client.verify_write_access()


def test_list_snapshot_folders(hugging_face_client: HuggingFaceClient) -> None:
    folders: list[HuggingFaceFolder] = hugging_face_client.list_snapshot_folders()
    assert folders
    for folder in folders:
        assert folder.startswith("history/")
        date.fromisoformat(folder.removeprefix("history/"))
