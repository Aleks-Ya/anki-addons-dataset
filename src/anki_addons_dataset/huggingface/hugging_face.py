import shutil
from pathlib import Path
from typing import Any

from anki_addons_dataset.common.json_helper import JsonHelper
from anki_addons_dataset.common.working_dir import VersionDir


class HuggingFace:

    @staticmethod
    def create_dataset_card(dataset_dir: Path) -> None:
        src_file: Path = Path(__file__).parent / "README.md"
        dest_file: Path = dataset_dir / "README.md"
        shutil.copy(src_file, dest_file)
        print(f"Created dataset card: {dest_file}")

    @staticmethod
    def create_version_metadata_yaml(version_dir: VersionDir) -> None:
        content: dict[str, Any] = {
            "creation_date": version_dir.version_dir_to_creation_date()
        }
        dest_file: Path = version_dir.get_metadata_json()
        JsonHelper.write_dict_to_file(content, dest_file)
        print(f"Created dataset metadata file: {dest_file}")
