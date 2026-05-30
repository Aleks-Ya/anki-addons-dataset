import shutil
from datetime import date
from functools import total_ordering
from pathlib import Path
from typing import Optional
import logging
from logging import Logger

from anki_addons_dataset.common.data_types import SnapshotDate

log: Logger = logging.getLogger(__name__)


@total_ordering
class SnapshotDir:
    def __init__(self, snapshot_dir: Path):
        self.__snapshot_dir: Path = snapshot_dir

    def get_path(self) -> Path:
        return self.__snapshot_dir

    def create(self) -> 'SnapshotDir':
        raw_dir: Path = self.get_raw_dir()
        stage_dir: Path = self.get_stage_dir()
        final_dir: Path = self.get_final_dir()
        self.__delete_dir(stage_dir)
        self.__delete_dir(final_dir)
        raw_dir.mkdir(parents=True, exist_ok=True)
        stage_dir.mkdir(parents=True, exist_ok=True)
        final_dir.mkdir(parents=True, exist_ok=True)
        log.info(f"Create raw dir: {raw_dir}")
        log.info(f"Create stage dir: {stage_dir}")
        log.info(f"Create final dir: {final_dir}")
        return self

    def get_raw_dir(self) -> Path:
        return self.__snapshot_dir / "1-raw"

    def get_stage_dir(self) -> Path:
        return self.__snapshot_dir / "2-stage"

    def get_final_dir(self) -> Path:
        return self.__snapshot_dir / "3-final"

    def snapshot_dir_to_snapshot_date(self) -> SnapshotDate:
        return SnapshotDate(date.fromisoformat(self.__snapshot_dir.name))

    def get_metadata_json(self) -> Path:
        return self.__snapshot_dir / "metadata.json"

    @staticmethod
    def __delete_dir(directory: Path) -> None:
        log.info(f"Deleting dir: {directory}")
        shutil.rmtree(directory, ignore_errors=True)

    def __lt__(self, other: 'SnapshotDir') -> bool:
        return self.snapshot_dir_to_snapshot_date() < other.snapshot_dir_to_snapshot_date()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SnapshotDir):
            return NotImplemented
        return self.__snapshot_dir == other.__snapshot_dir

    def __hash__(self) -> int:
        return hash(self.__snapshot_dir)

    def __str__(self) -> str:
        return str(self.__snapshot_dir)

    def __repr__(self) -> str:
        return self.__str__()


class WorkingDir:
    def __init__(self, working_dir_path: Path):
        self.__working_dir_path: Path = working_dir_path
        self.__history_dir: Path = self.__working_dir_path / "history"
        self.__bundle_dir: Path = self.__working_dir_path / "bundle"

    def get_path(self) -> Path:
        return self.__working_dir_path

    def get_history_dir(self) -> Path:
        return self.__history_dir

    def get_bundle_dir(self) -> Path:
        return self.__bundle_dir

    def get_snapshot_dir(self, snapshot_date: SnapshotDate) -> SnapshotDir:
        return SnapshotDir(self.__history_dir / snapshot_date.isoformat())

    def list_snapshot_dirs(self) -> list[SnapshotDir]:
        snapshot_dirs: list[SnapshotDir] = []
        if self.__history_dir.exists():
            for sub_dir in self.__history_dir.iterdir():
                if sub_dir.is_dir():
                    snapshot_dirs.append(SnapshotDir(sub_dir))
                else:
                    log.info(f"Skipping {sub_dir}")
        snapshot_dirs.sort()
        return snapshot_dirs

    def get_latest_snapshot_dir(self) -> Optional[SnapshotDir]:
        snapshot_dirs: list[SnapshotDir] = self.list_snapshot_dirs()
        if len(snapshot_dirs) == 0:
            return None
        return snapshot_dirs[len(snapshot_dirs) - 1]
