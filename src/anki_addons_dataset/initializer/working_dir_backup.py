import logging
import shutil
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Optional

from anki_addons_dataset.common.log import Log
from anki_addons_dataset.common.working_dir import WorkingDir

log: Logger = logging.getLogger(__name__)


class WorkingDirBackup:
    def __init__(self, working_dir: WorkingDir):
        self.__working_dir: WorkingDir = working_dir

    def backup_existing_content(self) -> None:
        working_dir_path: Path = self.__working_dir.get_path()
        if not working_dir_path.exists():
            return
        preserved: set[Path] = self.__preserved_entries()
        movable: list[Path] = [entry for entry in working_dir_path.iterdir() if entry not in preserved]
        if not movable:
            log.info(f"Nothing to back up in existing working dir '{working_dir_path}'")
            return
        current_time: str = datetime.today().strftime("%Y%m%d-%H%M%S")
        backup_dir: Path = self.__working_dir.get_backups_dir() / current_time
        log.info(f"Backing up existing working dir content to '{backup_dir}': "
                 f"{[entry.name for entry in movable]}")
        backup_dir.mkdir(parents=True, exist_ok=True)
        for entry in movable:
            shutil.move(entry, backup_dir / entry.name)
        log.info("Backed up existing working dir content")

    def __preserved_entries(self) -> set[Path]:
        preserved: set[Path] = {self.__working_dir.get_backups_dir()}
        log_entry: Optional[Path] = self.__active_log_entry()
        if log_entry:
            preserved.add(log_entry)
        return preserved

    def __active_log_entry(self) -> Optional[Path]:
        log_file: Optional[Path] = Log.active_log_file()
        if log_file is None:
            return None
        working_dir_path: Path = self.__working_dir.get_path().resolve()
        resolved_log_file: Path = log_file.resolve()
        if not resolved_log_file.is_relative_to(working_dir_path):
            return None
        return self.__working_dir.get_path() / resolved_log_file.relative_to(working_dir_path).parts[0]
