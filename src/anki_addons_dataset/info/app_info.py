import logging
import platform
import sys
from logging import Logger
from pathlib import Path
from typing import Optional

from anki_addons_dataset import __version__
from anki_addons_dataset.collector.github.github_rest_client import GithubRestClient
from anki_addons_dataset.common.data_types import SnapshotDate, ReportDate, PageLoadTimeout, ElementWaitTimeout
from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.config.app_config import AppConfig
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient

log: Logger = logging.getLogger(__name__)


class AppInfo:
    """Logs the app version and runtime configuration. Run first by the `all` operation."""

    def __init__(self, working_dir: WorkingDir, hugging_face_client: HuggingFaceClient, config: AppConfig,
                 page_load_timeout: PageLoadTimeout, element_wait_timeout: ElementWaitTimeout):
        self.__working_dir: WorkingDir = working_dir
        self.__hugging_face_client: HuggingFaceClient = hugging_face_client
        self.__config: AppConfig = config
        self.__page_load_timeout: PageLoadTimeout = page_load_timeout
        self.__element_wait_timeout: ElementWaitTimeout = element_wait_timeout

    def print_info(self, snapshot_date: Optional[SnapshotDate], report_date: ReportDate) -> None:
        log.info("=== Application info ===")
        log.info(f"Version: {__version__}")
        log.info(f"Python: {platform.python_version()} ({sys.executable})")
        log.info(f"Platform: {platform.platform()}")
        log.info(f"Working directory: {self.__working_dir.get_path()}")
        log.info(f"History directory: {self.__working_dir.get_history_dir()}")
        log.info(f"Bundle directory: {self.__working_dir.get_bundle_dir()}")
        log.info(f"Log file: {self.__config.resolved_logging().file or 'disabled'}")
        log.info(f"HuggingFace dataset: {self.__hugging_face_client.get_repo_id()}")
        log.info(f"GitHub token file: {self.__config.github.token_file}")
        log.info(f"AI endpoint: {self.__config.ai.endpoint}")
        log.info(f"AI model: {self.__config.ai.model}")
        log.info(f"AI key file: {self.__config.ai.api_key_file}")
        log.info(f"Snapshot date: {snapshot_date}")
        log.info(f"Report date: {report_date}")
        log.info(f"Page load timeout: {self.__page_load_timeout}s")
        log.info(f"Element wait timeout: {self.__element_wait_timeout}s")
        log.info(f"Addon sample: {self.__config.sample.addons or 'all addons'}")
        log.info(f"Snapshot sample: {self.__config.sample.snapshots or 'all snapshots'}")
        log.info("========================")
        self.__verify_github_token()
        self.__verify_ai_key_file()
        self.__verify_hugging_face_access()

    def __verify_github_token(self) -> None:
        token_file: Path = self.__config.github.token_file
        github_rest_client: GithubRestClient = GithubRestClient(offline=False, token_file=token_file)
        limit_remaining: Optional[int] = github_rest_client.verify_token()
        log.info(f"GitHub token: OK ({token_file}, {limit_remaining} API requests remaining)")

    def __verify_ai_key_file(self) -> None:
        """Only checks the file: a live request would bill every `info` run."""
        api_key_file: Path = self.__config.ai.api_key_file
        if not api_key_file.is_file():
            raise FileNotFoundError(f"Missing AI API key file: {api_key_file}")
        if not api_key_file.read_text().strip():
            raise ValueError(f"Empty AI API key file: {api_key_file}")
        log.info(f"AI API key: OK ({api_key_file})")

    def __verify_hugging_face_access(self) -> None:
        self.__hugging_face_client.verify_write_access()
        log.info(f"HuggingFace write access: OK ({self.__hugging_face_client.get_repo_id()})")
