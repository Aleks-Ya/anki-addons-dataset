import json
from pathlib import Path

from anki_addons_dataset.common.working_dir import SnapshotDir


class PackageList:

    @staticmethod
    def write(snapshot_dir: SnapshotDir) -> None:
        package_dir: Path = snapshot_dir.get_package_dir()
        entries: list[str] = sorted(file.relative_to(package_dir).as_posix()
                                    for file in package_dir.glob("*/*.ankiaddon"))
        snapshot_dir.get_package_list_file().write_text(json.dumps(entries, indent=2))

    @staticmethod
    def read(snapshot_dir: SnapshotDir) -> list[str]:
        list_file: Path = snapshot_dir.get_package_list_file()
        if not list_file.exists():
            return []
        return json.loads(list_file.read_text())
