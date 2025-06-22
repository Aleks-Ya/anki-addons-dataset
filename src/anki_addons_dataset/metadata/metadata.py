import json
from pathlib import Path
from typing import Any


class Metadata:
    def __init__(self, dataset_dir: Path):
        self.__dataset_dir: Path = dataset_dir

    def create_dataset_metadata_file(self) -> None:
        src_dir: Path = Path(__file__).parent
        template_file: Path = src_dir / "dataset-metadata-template.json"
        with open(template_file, 'r') as fp:
            template: dict[str, Any] = json.load(fp)
        description: str = (src_dir / "dataset-description.md").read_text()
        template["description"] = description
        dest_file: Path = self.__dataset_dir / "dataset-metadata.json"
        with open(dest_file, 'w') as fp:
            json.dump(template, fp, indent=2)
        print(f"Created metadata file: {dest_file}")
