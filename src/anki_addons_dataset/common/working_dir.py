from datetime import date
from pathlib import Path


class WorkingDir:
    def __init__(self, working_dir: Path):
        self.__working_dir: Path = working_dir
        self.__history_dir: Path = self.__working_dir / "history"

    def get_working_dir(self) -> Path:
        return self.__working_dir

    def get_history_dir(self) -> Path:
        return self.__history_dir

    def list_version_dirs(self) -> list[Path]:
        version_dirs: list[Path] = []
        for sub_dir in self.__history_dir.iterdir():
            if sub_dir.is_dir():
                version_dirs.append(sub_dir)
            else:
                print(f"Skipping {sub_dir}")
        return version_dirs

    @staticmethod
    def version_dir_to_creation_date(version_dir: Path) -> date:
        return date.fromisoformat(version_dir.name)
