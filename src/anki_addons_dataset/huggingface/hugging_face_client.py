from pathlib import Path
import logging
from logging import Logger
from shutil import rmtree
from typing import Iterable

from huggingface_hub import HfApi, RepoFolder, RepoFile
from huggingface_hub.errors import EntryNotFoundError, RepositoryNotFoundError, HfHubHTTPError

from anki_addons_dataset.common.data_types import HuggingFaceFolder

log: Logger = logging.getLogger(__name__)


class HuggingFaceClient:
    __repo_id: str = "Ya-Alex/anki-addons"
    __synced_dirs: list[str] = ["history", "latest"]

    def __init__(self, hf_api: HfApi):
        self.__api: HfApi = hf_api

    def get_repo_id(self) -> str:
        return self.__repo_id

    def upload_dataset(self, bundle_dir: Path) -> None:
        self.__verify_write_access()
        hf_cache_dir: Path = bundle_dir / ".cache"
        if hf_cache_dir.exists():
            log.info(f"Deleting HF cache folder: {hf_cache_dir}")
            rmtree(hf_cache_dir)
        log.info(f"Uploading dataset: {self.__repo_id}")
        self.__api.upload_large_folder(folder_path=bundle_dir, repo_id=self.__repo_id, repo_type="dataset")
        log.info(f"Uploaded dataset: {self.__repo_id}")

    def prune_orphans(self, bundle_dir: Path) -> None:
        local_files: set[str] = self.__local_repo_files(bundle_dir)
        orphans: list[str] = self.__remote_orphans(local_files)
        if not orphans:
            log.info(f"No orphan files to prune in dataset: {self.__repo_id}")
            return
        log.info(f"Pruning {len(orphans)} orphan files from dataset: {self.__repo_id}")
        for orphan in orphans:
            log.info(f"Orphan file: {orphan}")
        self.__api.delete_files(
            repo_id=self.__repo_id, repo_type="dataset", delete_patterns=orphans,
            commit_message="Prune files removed from the local bundle")
        log.info(f"Pruned {len(orphans)} orphan files from dataset: {self.__repo_id}")

    def list_snapshot_folders(self) -> list[HuggingFaceFolder]:
        files: list[RepoFile | RepoFolder] = list(self.__api.list_repo_tree(
            self.__repo_id, repo_type="dataset", path_in_repo="history"))
        folders: list[RepoFolder] = [f for f in files if isinstance(f, RepoFolder)]
        return [HuggingFaceFolder(f.path) for f in folders]

    def download_file(self, file_path: str) -> Path:
        return Path(self.__api.hf_hub_download(repo_id=self.__repo_id, filename=file_path, repo_type="dataset"))

    def __verify_write_access(self) -> None:
        try:
            self.__api.auth_check(self.__repo_id, repo_type="dataset", write=True)
        except (RepositoryNotFoundError, HfHubHTTPError) as e:
            status_code = getattr(getattr(e, "response", None), "status_code", None)
            if status_code in (401, 403):
                raise PermissionError(f"HuggingFace unauthorized: {self.__repo_id}") from e
            raise

    @staticmethod
    def __local_repo_files(bundle_dir: Path) -> set[str]:
        local_files: set[str] = set()
        for top in HuggingFaceClient.__synced_dirs:
            top_dir: Path = bundle_dir / top
            if not top_dir.exists():
                continue
            for file in top_dir.rglob("*"):
                if file.is_file():
                    local_files.add(file.relative_to(bundle_dir).as_posix())
        return local_files

    def __remote_orphans(self, local_files: set[str]) -> list[str]:
        orphans: list[str] = []
        for top in self.__synced_dirs:
            try:
                tree: Iterable[RepoFile | RepoFolder] = self.__api.list_repo_tree(
                    self.__repo_id, repo_type="dataset", path_in_repo=top, recursive=True)
            except EntryNotFoundError:
                log.info(f"Remote folder not found, nothing to prune: {top}")
                continue
            for entry in tree:
                if isinstance(entry, RepoFile) and entry.path not in local_files:
                    orphans.append(entry.path)
        return orphans
