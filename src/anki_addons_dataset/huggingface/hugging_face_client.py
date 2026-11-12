from pathlib import Path
import logging
from logging import Logger
from shutil import rmtree
from typing import Iterable

from huggingface_hub import HfApi, RepoFolder, RepoFile, GitRefs
from huggingface_hub.errors import EntryNotFoundError, RepositoryNotFoundError, HfHubHTTPError

from anki_addons_dataset.common.data_types import HuggingFaceFolder, DatasetVersion, SnapshotDate
from anki_addons_dataset.config.app_config import HuggingFaceConfig

log: Logger = logging.getLogger(__name__)


class HuggingFaceClient:

    def __init__(self, hf_api: HfApi, config: HuggingFaceConfig):
        self.__api: HfApi = hf_api
        self.__repo_id: str = config.repo_id
        self.__synced_dirs: list[str] = config.synced_dirs

    def get_repo_id(self) -> str:
        return self.__repo_id

    def upload_dataset(self, bundle_dir: Path) -> None:
        self.verify_write_access()
        hf_cache_dir: Path = bundle_dir / ".cache"
        if hf_cache_dir.exists():
            log.info(f"Deleting HF cache folder: {hf_cache_dir}")
            rmtree(hf_cache_dir)
        log.info(f"Uploading dataset: {self.__repo_id}")
        self.__api.upload_folder(folder_path=bundle_dir, repo_id=self.__repo_id, repo_type="dataset")
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

    def publish_release(self, dataset_version: DatasetVersion, snapshot_date: SnapshotDate) -> None:
        refs: GitRefs = self.__api.list_repo_refs(self.__repo_id, repo_type="dataset")
        head: str = next(branch.target_commit for branch in refs.branches if branch.name == "main")
        tag: str = self.__release_tag(dataset_version, snapshot_date, {t.name for t in refs.tags})
        self.__api.create_tag(self.__repo_id, repo_type="dataset", tag=tag, revision=head,
                              tag_message=f"Dataset {dataset_version}, snapshot {snapshot_date.isoformat()}")
        log.info(f"Created release tag: {tag}")
        major_branch: str = f"v{dataset_version.split('.')[0]}"
        if any(branch.name == major_branch for branch in refs.branches):
            self.__api.delete_branch(self.__repo_id, repo_type="dataset", branch=major_branch)
        self.__api.create_branch(self.__repo_id, repo_type="dataset", branch=major_branch, revision=head)
        log.info(f"Pointed branch {major_branch} at {head}")

    def list_snapshot_folders(self) -> list[HuggingFaceFolder]:
        files: list[RepoFile | RepoFolder] = list(self.__api.list_repo_tree(
            self.__repo_id, repo_type="dataset", path_in_repo="history"))
        folders: list[RepoFolder] = [f for f in files if isinstance(f, RepoFolder)]
        return [HuggingFaceFolder(f.path) for f in folders]

    def download_file(self, file_path: str) -> Path:
        return Path(self.__api.hf_hub_download(repo_id=self.__repo_id, filename=file_path, repo_type="dataset"))

    def download_packages(self) -> Path:
        return Path(self.__api.snapshot_download(repo_id=self.__repo_id, repo_type="dataset",
                                                 allow_patterns="packages/*"))

    def verify_write_access(self) -> None:
        """Fail fast if the configured credentials cannot write to the dataset.

        Called by the `info` step as a preflight check and again by `upload_dataset`
        before it pushes anything."""
        try:
            self.__api.auth_check(self.__repo_id, repo_type="dataset", write=True)
        except (RepositoryNotFoundError, HfHubHTTPError) as e:
            status_code = getattr(getattr(e, "response", None), "status_code", None)
            if status_code in (401, 403):
                raise PermissionError(f"HuggingFace unauthorized: {self.__repo_id}") from e
            raise

    @staticmethod
    def __release_tag(dataset_version: DatasetVersion, snapshot_date: SnapshotDate, existing_tags: set[str]) -> str:
        base: str = f"v{dataset_version}-{snapshot_date.isoformat()}"
        tag: str = base
        suffix: int = 2
        while tag in existing_tags:
            tag = f"{base}-{suffix}"
            suffix += 1
        return tag

    def __local_repo_files(self, bundle_dir: Path) -> set[str]:
        local_files: set[str] = set()
        for top in self.__synced_dirs:
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
