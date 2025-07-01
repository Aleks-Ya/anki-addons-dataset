from datetime import date
from pathlib import Path
from typing import Optional


class WorkingDir:
    def __init__(self, working_dir: Path):
        self.__working_dir: Path = working_dir
        self.__history_dir: Path = self.__working_dir / "history"

    def get_working_dir(self) -> Path:
        return self.__working_dir

    def get_history_dir(self) -> Path:
        return self.__history_dir

    @staticmethod
    def get_final_dir(version_dir: Path) -> Path:
        return version_dir / "3-final"

    def list_version_dirs(self) -> list[Path]:
        version_dirs: list[Path] = []
        for sub_dir in self.__history_dir.iterdir():
            if sub_dir.is_dir():
                version_dirs.append(sub_dir)
            else:
                print(f"Skipping {sub_dir}")
        return version_dirs

    def get_latest_version_dir(self) -> Optional[Path]:
        version_dirs: list[Path] = self.list_version_dirs()
        if len(version_dirs) == 0:
            return None
        version_dates: list[date] = [date.fromisoformat(version_dir.name) for version_dir in version_dirs]
        version_dates.sort()
        return version_dirs[0]

    @staticmethod
    def version_dir_to_creation_date(version_dir: Path) -> date:
        return date.fromisoformat(version_dir.name)

    @staticmethod
    def get_metadata_json(version_dir: Path) -> Path:
        return version_dir / "metadata.json"
