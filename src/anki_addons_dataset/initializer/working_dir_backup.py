import logging
import shutil
from datetime import datetime
from logging import Logger
from pathlib import Path

from anki_addons_dataset.common.working_dir import WorkingDir

log: Logger = logging.getLogger(__name__)


class WorkingDirBackup:
    def __init__(self, working_dir: WorkingDir):
        self.__working_dir: WorkingDir = working_dir

    def rename_existing_working_dir(self) -> None:
        if self.__working_dir.get_path().exists():
            current_time: str = datetime.today().strftime("%Y%m%d-%H%M%S")
            backup_working_dir_name: str = f"{self.__working_dir.get_path().name}.bak-{current_time}"
            backup_working_dir: Path = self.__working_dir.get_path().parent / backup_working_dir_name
            log.info(f"Renaming existing working dir '{self.__working_dir.get_path()}' to '{backup_working_dir}'")
            shutil.move(self.__working_dir.get_path(), backup_working_dir)
            log.info("Renamed existing working dir")
