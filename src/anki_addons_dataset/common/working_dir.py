from datetime import date
from pathlib import Path
from typing import Optional


class VersionDir:
    def __init__(self, version_dir: Path):
        self.__version_dir: Path = version_dir

    def get_path(self) -> Path:
        return self.__version_dir

    def create(self) -> 'VersionDir':
        self.__version_dir.mkdir(parents=True, exist_ok=True)
        return self

    def get_raw_dir(self) -> Path:
        return self.__version_dir / "1-raw"

    def get_stage_dir(self) -> Path:
        return self.__version_dir / "2-stage"

    def get_final_dir(self) -> Path:
        return self.__version_dir / "3-final"

    def version_dir_to_creation_date(self) -> date:
        return date.fromisoformat(self.__version_dir.name)

    def get_metadata_json(self) -> Path:
        return self.__version_dir / "metadata.json"

    def __lt__(self, other: 'VersionDir') -> bool:
        return self.version_dir_to_creation_date() < other.version_dir_to_creation_date()

    def __gt__(self, other: 'VersionDir') -> bool:
        return self.version_dir_to_creation_date() > other.version_dir_to_creation_date()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionDir):
            return NotImplemented
        return self.__version_dir == other.__version_dir

    def __str__(self) -> str:
        return str(self.__version_dir)

    def __repr__(self) -> str:
        return self.__str__()


class WorkingDir:
    def __init__(self, working_dir_path: Path):
        self.__working_dir_path: Path = working_dir_path
        self.__history_dir: Path = self.__working_dir_path / "history"

    def get_path(self) -> Path:
        return self.__working_dir_path

    def get_history_dir(self) -> Path:
        return self.__history_dir

    def get_version_dir(self, creation_date: date) -> VersionDir:
        return VersionDir(self.__history_dir / creation_date.isoformat())

    def list_version_dirs(self) -> list[VersionDir]:
        version_dirs: list[VersionDir] = []
        if self.__history_dir.exists():
            for sub_dir in self.__history_dir.iterdir():
                if sub_dir.is_dir():
                    version_dirs.append(VersionDir(sub_dir))
                else:
                    print(f"Skipping {sub_dir}")
        version_dirs.sort()
        return version_dirs

    def get_latest_version_dir(self) -> Optional[VersionDir]:
        version_dirs: list[VersionDir] = self.list_version_dirs()
        if len(version_dirs) == 0:
            return None
        return version_dirs[len(version_dirs) - 1]
