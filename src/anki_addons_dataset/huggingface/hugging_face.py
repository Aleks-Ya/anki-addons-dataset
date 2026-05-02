import shutil
from pathlib import Path
import logging
from logging import Logger

log: Logger = logging.getLogger(__name__)


class HuggingFace:

    @staticmethod
    def create_dataset_card(bundle_dir: Path) -> None:
        src_file: Path = Path(__file__).parent / "README.md"
        dest_file: Path = bundle_dir / "README.md"
        shutil.copy(src_file, dest_file)
        log.info(f"Created dataset card: {dest_file}")
