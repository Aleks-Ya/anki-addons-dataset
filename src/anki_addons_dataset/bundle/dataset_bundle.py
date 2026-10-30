import logging
import shutil
from logging import Logger
from pathlib import Path
from typing import Optional
from zipfile import ZIP_DEFLATED, ZipFile

from anki_addons_dataset.common.data_types import SnapshotDate
from anki_addons_dataset.common.file_links import FileLinks
from anki_addons_dataset.common.working_dir import WorkingDir, SnapshotDir
from anki_addons_dataset.huggingface.hugging_face import HuggingFace

log: Logger = logging.getLogger(__name__)


class DatasetBundle:
    def __init__(self, working_dir: WorkingDir):
        self.__working_dir: WorkingDir = working_dir

    def create_bundle(self) -> None:
        bundle_dir: Path = self.__working_dir.get_bundle_dir()
        log.info(f"Creating bundle in {bundle_dir}")
        shutil.rmtree(bundle_dir, ignore_errors=True)
        self.__copy_snapshots(bundle_dir)
        self.__link_packages(bundle_dir)
        self.__copy_latest_snapshot(bundle_dir)
        HuggingFace.create_dataset_card(bundle_dir)

    def __copy_snapshots(self, bundle_dir: Path):
        bundle_history_dir: Path = bundle_dir / "history"
        bundle_history_dir.mkdir(parents=True, exist_ok=True)
        for snapshot_dir in self.__working_dir.list_sampled_snapshot_dirs():
            snapshot_date: SnapshotDate = snapshot_dir.snapshot_dir_to_snapshot_date()
            base_name: str = f"{snapshot_date}"
            output_dir: Path = bundle_history_dir / base_name
            self.__create_zip(snapshot_dir.get_raw_dir(), output_dir, "raw", snapshot_dir.get_package_dir())
            self.__create_zip(snapshot_dir.get_stage_dir(), output_dir, "stage")
            log.info(f"Copying {snapshot_dir.get_final_dir()} to {output_dir}")
            shutil.copytree(snapshot_dir.get_final_dir(), output_dir, dirs_exist_ok=True)
            src_metadata_file: Path = snapshot_dir.get_metadata_json()
            dest_metadata_file: Path = output_dir / src_metadata_file.name
            log.info(f"Copying {src_metadata_file} to {dest_metadata_file}")
            shutil.copyfile(src_metadata_file, dest_metadata_file)

    def __link_packages(self, bundle_dir: Path) -> None:
        bundle_packages_dir: Path = bundle_dir / "packages"
        for snapshot_dir in self.__working_dir.list_sampled_snapshot_dirs():
            package_dir: Path = snapshot_dir.get_package_dir()
            for file in package_dir.glob("*/*.ankiaddon"):
                FileLinks.link_or_copy(file, bundle_packages_dir / file.relative_to(package_dir))

    def __copy_latest_snapshot(self, bundle_dir: Path):
        latest_dir: Path = bundle_dir / "latest"
        log.info(f"Copying the latest snapshot: {latest_dir}")
        latest_snapshot_dir: Optional[SnapshotDir] = self.__working_dir.get_latest_snapshot_dir()
        if not latest_snapshot_dir:
            raise ValueError("No snapshots found")
        final_dir: Path = latest_snapshot_dir.get_final_dir()
        shutil.copytree(final_dir, latest_dir)
        src_metadata_file: Path = latest_snapshot_dir.get_metadata_json()
        dest_metadata_file: Path = latest_dir / src_metadata_file.name
        log.info(f"Copying {src_metadata_file} to {dest_metadata_file}")
        shutil.copyfile(src_metadata_file, dest_metadata_file)

    @staticmethod
    def __create_zip(source_dir: Path, output_dir: Path, output_base_name: str,
                     excluded_dir: Optional[Path] = None) -> None:
        zip_file: Path = output_dir / f"{output_base_name}.zip"
        log.info(f"Creating zip: {zip_file}")
        output_dir.mkdir(parents=True, exist_ok=True)
        with ZipFile(zip_file, "w", ZIP_DEFLATED) as archive:
            for path in sorted(source_dir.rglob("*")):
                if excluded_dir is None or not path.is_relative_to(excluded_dir):
                    archive.write(path, path.relative_to(source_dir))
