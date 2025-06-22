import shutil
from pathlib import Path


class HuggingFace:
    def __init__(self, dataset_dir: Path):
        self.__dataset_dir: Path = dataset_dir

    def create_dataset_card(self) -> None:
        src_file: Path = Path(__file__).parent / "README.md"
        dest_file: Path = self.__dataset_dir / "README.md"
        shutil.copy(src_file, dest_file)
        print(f"Created dataset card: {dest_file}")
