import json
from abc import abstractmethod, ABC
from pathlib import Path
from typing import Any, Optional
import logging
from logging import Logger

from requests import Response

from anki_addons_dataset.common.data_types import GithubRepo
from anki_addons_dataset.common.json_helper import JsonHelper

log: Logger = logging.getLogger(__name__)


class RepoHandler(ABC):
    def __init__(self, repo: GithubRepo, raw_dir: Path, stage_dir: Path,
                 prev_raw_dir: Optional[Path] = None) -> None:
        self._repo: GithubRepo = repo
        self.__raw_dir: Path = raw_dir
        self.__stage_dir: Path = stage_dir
        self.__prev_raw_dir: Optional[Path] = prev_raw_dir

    def is_downloaded(self) -> bool:
        return self.get_raw_file().exists()

    def get_not_found_return_value(self) -> Any:
        return None

    def status_200(self, response: Response) -> None:
        raw_file: Path = self.get_raw_file()
        JsonHelper.write_content_to_file(response.text, raw_file)
        etag: Optional[str] = response.headers.get("ETag")
        if etag:
            self.__write_etag(etag)

    def status_304(self) -> None:
        prev_raw_file: Optional[Path] = self.__get_prev_raw_file()
        prev_etag: Optional[str] = self.get_prev_etag()
        if prev_raw_file is None or prev_etag is None:
            raise RuntimeError(f"Got 304 without a cached previous snapshot for {self._repo.get_id()}")
        JsonHelper.write_content_to_file(prev_raw_file.read_text(), self.get_raw_file())
        self.__write_etag(prev_etag)

    def status_404(self) -> None:
        raw_file: Path = self.get_raw_file()
        url: str = self.get_url()
        log.info(f"Repo not found: {url}")
        JsonHelper.write_dict_to_file({}, raw_file)
        self.__get_not_found_file().touch()

    def status_409(self, response: Response) -> None:
        self.status_other(response)

    def status_other(self, response: Response) -> None:
        raise RuntimeError(f"Error status {response.status_code} for {self._repo.get_id()}: {response.text}")

    @abstractmethod
    def get_url(self) -> str:
        ...

    def get_raw_file(self) -> Path:
        return self.__raw_dir / self._repo.user / self._repo.repo_name / f"{self._get_raw_filename()}.json"

    def get_etag_file(self) -> Path:
        return self.__raw_dir / self._repo.user / self._repo.repo_name / f"{self._get_raw_filename()}.etag"

    def get_prev_etag(self) -> Optional[str]:
        prev_raw_file: Optional[Path] = self.__get_prev_raw_file()
        prev_etag_file: Optional[Path] = self.__get_prev_etag_file()
        if prev_raw_file is None or prev_etag_file is None:
            return None
        if not prev_raw_file.exists() or not prev_etag_file.exists():
            return None
        return prev_etag_file.read_text().strip()

    def get_stage_file(self) -> Path:
        return self.__stage_dir / self._repo.user / self._repo.repo_name / f"{self._get_stage_filename()}.json"

    def extract_return_value(self) -> Optional[Any]:
        try:
            raw_file: Path = self.get_raw_file()
            content_dict: object = json.loads(raw_file.read_text())
            return self._extract_return_value_from_dict(content_dict)
        except Exception as e:
            raise RuntimeError(f"Error while extracting return value for {self._repo.get_id()}") from e

    def write_stage(self, return_value: Any) -> None:
        stage_dict: dict[str, Any] = self._prepare_stage_dict(return_value)
        stage_file: Path = self.get_stage_file()
        JsonHelper.write_dict_to_file(stage_dict, stage_file)

    def is_repo_marked_as_not_found(self) -> bool:
        return self.__get_not_found_file().exists()

    @abstractmethod
    def _get_raw_filename(self) -> str:
        ...

    @abstractmethod
    def _get_stage_filename(self) -> str:
        ...

    @abstractmethod
    def _extract_return_value_from_dict(self, content_obj: object) -> Any:
        ...

    @abstractmethod
    def _prepare_stage_dict(self, return_value: Any) -> dict[str, Any]:
        ...

    def __get_not_found_file(self) -> Path:
        return self.__raw_dir / self._repo.user / self._repo.repo_name / "NOT_FOUND_404"

    def __write_etag(self, etag: str) -> None:
        etag_file: Path = self.get_etag_file()
        etag_file.parent.mkdir(parents=True, exist_ok=True)  # plain text: ETags like W/"..." are not JSON
        etag_file.write_text(etag)

    def __get_prev_raw_file(self) -> Optional[Path]:
        if self.__prev_raw_dir is None:
            return None
        return self.__prev_raw_dir / self._repo.user / self._repo.repo_name / f"{self._get_raw_filename()}.json"

    def __get_prev_etag_file(self) -> Optional[Path]:
        if self.__prev_raw_dir is None:
            return None
        return self.__prev_raw_dir / self._repo.user / self._repo.repo_name / f"{self._get_raw_filename()}.etag"
