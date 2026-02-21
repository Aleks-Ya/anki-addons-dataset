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
    def __init__(self, repo: GithubRepo, raw_dir: Path, stage_dir: Path) -> None:
        self._repo: GithubRepo = repo
        self.__raw_dir: Path = raw_dir
        self.__stage_dir: Path = stage_dir

    def is_downloaded(self) -> bool:
        return self.get_raw_file().exists()

    def get_not_found_return_value(self) -> Any:
        return None

    def status_200(self, response: Response) -> None:
        raw_file: Path = self.get_raw_file()
        JsonHelper.write_content_to_file(response.text, raw_file)

    def status_404(self) -> None:
        raw_file: Path = self.get_raw_file()
        url: str = self.get_url()
        log.info(f"Repo not found: {url}")
        JsonHelper.write_dict_to_file({}, raw_file)
        self.__get_not_found_file().write_text("")

    def status_409(self, response: Response) -> None:
        self.status_other(response)

    def status_other(self, response: Response) -> None:
        raise RuntimeError(f"Error status {response.status_code} for {self._repo.get_id()}: {response.text}")

    @abstractmethod
    def get_url(self) -> str:
        ...

    def get_raw_file(self) -> Path:
        name: str = self.__get_json_filename(self._get_raw_filename())
        return self.__raw_dir / self._repo.user / self._repo.repo_name / f"{name}.json"

    def get_stage_file(self) -> Path:
        name: str = self.__get_json_filename(self._get_stage_filename())
        return self.__stage_dir / self._repo.user / self._repo.repo_name / f"{name}.json"

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
        name: str = self.__get_json_filename("NOT_FOUND_404")
        return self.__raw_dir / self._repo.user / self._repo.repo_name / name

    def __get_json_filename(self, name: str) -> str:
        return f"{self._repo.user}_{self._repo.repo_name}_{name}"
