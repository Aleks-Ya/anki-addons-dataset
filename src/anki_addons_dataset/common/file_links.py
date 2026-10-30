import logging
import os
import shutil
from logging import Logger
from pathlib import Path

log: Logger = logging.getLogger(__name__)


class FileLinks:

    @staticmethod
    def link_or_copy(source: Path, target: Path) -> None:
        if target.exists():
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        real_source: Path = source.resolve()
        try:
            os.link(real_source, target)
        except OSError as e:
            log.debug(f"Cannot hardlink {real_source} to {target}, copying instead: {e}")
            part_file: Path = target.with_name(f"{target.name}.part")
            shutil.copy2(real_source, part_file)
            os.replace(part_file, target)
