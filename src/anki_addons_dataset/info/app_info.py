import logging
import platform
import sys
from logging import Logger
from typing import Optional

from anki_addons_dataset import __version__
from anki_addons_dataset.collector.github.github_rest_client import GithubRestClient
from anki_addons_dataset.common.data_types import SnapshotDate, ReportDate
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient

log: Logger = logging.getLogger(__name__)


class AppInfo:
    """Logs the app version and runtime configuration. Run first by the `all` operation."""

    def __init__(self, working_dir: WorkingDir, hugging_face_client: HuggingFaceClient):
        self.__working_dir: WorkingDir = working_dir
        self.__hugging_face_client: HuggingFaceClient = hugging_face_client

    def print_info(self, snapshot_date: Optional[SnapshotDate], report_date: ReportDate) -> None:
        log.info("=== Application info ===")
        log.info(f"Version: {__version__}")
        log.info(f"Python: {platform.python_version()} ({sys.executable})")
        log.info(f"Platform: {platform.platform()}")
        log.info(f"Working directory: {self.__working_dir.get_path()}")
        log.info(f"History directory: {self.__working_dir.get_history_dir()}")
        log.info(f"Bundle directory: {self.__working_dir.get_bundle_dir()}")
        log.info(f"HuggingFace dataset: {self.__hugging_face_client.get_repo_id()}")
        log.info(f"GitHub token file: {GithubRestClient.get_token_file()}")
        log.info(f"Snapshot date: {snapshot_date}")
        log.info(f"Report date: {report_date}")
        log.info("========================")
        self.__verify_github_token()
        self.__verify_hugging_face_access()

    @staticmethod
    def __verify_github_token() -> None:
        GithubRestClient.read_token()
        log.info(f"GitHub token: OK ({GithubRestClient.get_token_file()})")

    def __verify_hugging_face_access(self) -> None:
        self.__hugging_face_client.verify_write_access()
        log.info(f"HuggingFace write access: OK ({self.__hugging_face_client.get_repo_id()})")
