import logging
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from logging import Logger
from pathlib import Path
from threading import local
from typing import Callable, Optional
from urllib.parse import parse_qs, urlsplit

from requests import RequestException, Response, Session

from anki_addons_dataset.common.data_types import AddonId, AnkiPointVersion

log: Logger = logging.getLogger(__name__)


class PackageError(Exception):
    pass


@dataclass(frozen=True)
class PackageLocation:
    path: str
    min_point_version: AnkiPointVersion
    uploaded: date


class PackageClient:
    __base_url: str = "https://ankiweb.net"
    __timeout_seconds: int = 60
    __attempts: int = 4
    __chunk_size: int = 1024 * 1024
    __retryable_statuses: frozenset[int] = frozenset({429, 500, 502, 503, 504})

    def __init__(self, session_factory: Callable[[], Session] = Session, retry_delay_seconds: int = 5) -> None:
        self.__session_factory: Callable[[], Session] = session_factory
        self.__retry_delay_seconds: int = retry_delay_seconds
        self.__thread_local: local = local()

    def locate(self, addon_id: AddonId, point_version: AnkiPointVersion) -> Optional[PackageLocation]:
        url: str = f"{self.__base_url}/shared/download/{addon_id}?v=2.1&p={point_version}"
        return self.__with_retries(lambda: self.__locate_once(url))

    def download(self, location: PackageLocation, part_file: Path) -> bool:
        url: str = f"{self.__base_url}{location.path}"
        return self.__with_retries(lambda: self.__download_once(url, part_file))

    def __locate_once(self, url: str) -> Optional[PackageLocation]:
        response: Response = self.__session().get(url, allow_redirects=False, timeout=self.__timeout_seconds)
        if response.status_code == 404:
            return None
        self.__check_status(response)
        location_path: Optional[str] = response.headers.get("location")
        if location_path is None:
            raise PackageError(f"No redirect from {url}: {response.status_code}")
        return self.__parse_location(location_path)

    def __download_once(self, url: str, part_file: Path) -> bool:
        with self.__session().get(url, stream=True, timeout=self.__timeout_seconds) as response:
            if response.status_code == 404:
                return False
            self.__check_status(response)
            with part_file.open("wb") as file:
                for chunk in response.iter_content(chunk_size=self.__chunk_size):
                    file.write(chunk)
        return True

    def __with_retries[T](self, action: Callable[[], T]) -> T:
        for attempt in range(1, self.__attempts):
            try:
                return action()
            except RequestException as e:
                log.info(f"Package request failed (attempt {attempt}): {e}")
                time.sleep(attempt * self.__retry_delay_seconds)
        return action()

    def __session(self) -> Session:
        if not hasattr(self.__thread_local, "session"):
            self.__thread_local.session = self.__session_factory()
        return self.__thread_local.session

    @staticmethod
    def __check_status(response: Response) -> None:
        if response.status_code in PackageClient.__retryable_statuses:
            raise RequestException(f"Status {response.status_code}: {response.url}")
        if response.status_code >= 400:
            raise PackageError(f"Status {response.status_code}: {response.url}")

    @staticmethod
    def __parse_location(location_path: str) -> PackageLocation:
        query: dict[str, list[str]] = parse_qs(urlsplit(location_path).query)
        try:
            uploaded: date = datetime.fromtimestamp(int(query["t"][0]), timezone.utc).date()
            return PackageLocation(location_path, AnkiPointVersion(int(query["minpt"][0])), uploaded)
        except (KeyError, ValueError, OverflowError, OSError) as e:
            raise PackageError(f"Unexpected download location {location_path}: {e!r}") from e
