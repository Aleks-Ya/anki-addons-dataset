import shutil
from datetime import date
from pathlib import Path
from typing import Any

from anki_addons_dataset.common.json_helper import JsonHelper


class HuggingFace:
    def __init__(self, final_dir: Path, creation_date: date):
        self.__final_dir: Path = final_dir
        self.__creation_date: date = creation_date

    def create_dataset_card(self) -> None:
        src_file: Path = Path(__file__).parent / "README.md"
        dest_file: Path = self.__final_dir / "README.md"
        shutil.copy(src_file, dest_file)
        print(f"Created dataset card: {dest_file}")

    def create_metadata_yaml(self) -> None:
        content: dict[str, Any] = {
            "creation_date": self.__creation_date
        }
        dest_file: Path = self.__final_dir / "metadata.json"
        JsonHelper.write_dict_to_file(content, dest_file)
        print(f"Created dataset metadata file: {dest_file}")
