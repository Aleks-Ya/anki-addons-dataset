from pathlib import Path
import logging
from logging import Logger
from shutil import rmtree

from huggingface_hub import HfApi
from huggingface_hub.errors import EntryNotFoundError

log: Logger = logging.getLogger(__name__)


class HuggingFaceClient:
    __repo_id: str = "Ya-Alex/anki-addons"

    def __init__(self, hf_api: HfApi):
        self.__api: HfApi = hf_api

    def upload_dataset(self, bundle_dir: Path) -> None:
        hf_cache_dir: Path = bundle_dir / ".cache"
        if hf_cache_dir.exists():
            log.info(f"Deleting HF cache folder: {hf_cache_dir}")
            rmtree(hf_cache_dir)
        log.info(f"Uploading dataset: {self.__repo_id}")
        self.__api.upload_large_folder(folder_path=bundle_dir, repo_id=self.__repo_id, repo_type="dataset")
        log.info(f"Uploaded dataset: {self.__repo_id}")

    def delete_dataset(self) -> None:
        log.info(f"Deleting dataset: {self.__repo_id}")
        try:
            self.__api.delete_folder(path_in_repo="history", repo_id=self.__repo_id, repo_type="dataset")
        except EntryNotFoundError:
            log.info(f"History folder not found for dataset: {self.__repo_id}")
            pass
        try:
            self.__api.delete_folder(path_in_repo="latest", repo_id=self.__repo_id, repo_type="dataset")
        except EntryNotFoundError:
            log.info(f"Latest folder not found for dataset: {self.__repo_id}")
            pass
        log.info(f"Deleted dataset: {self.__repo_id}")
