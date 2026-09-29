import os
from abc import ABC, abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Optional
import logging
from logging import Logger

from anki_addons_dataset.common.data_types import AddonInfo, AddonInfos

log: Logger = logging.getLogger(__name__)


class Enricher(ABC):

    def __init__(self, name: str, pool_size: int = 1):
        self.__name: str = name
        self.__pool_size: int = pool_size
        self.__executor: Optional[ThreadPoolExecutor] = None
        self.__futures: list[Future[None]] = []

    def start(self) -> None:
        log.info(f"Start thread pool: {self.__name} (size: {self.__pool_size})")
        self.__executor = ThreadPoolExecutor(max_workers=self.__pool_size, thread_name_prefix=self.__name)

    def download_in_background(self, addon_info: AddonInfo) -> None:
        log.debug(f"Enqueue for enriching ({self.__name}): {addon_info.header.id}")
        if self.__executor is None:
            raise RuntimeError(f"Enricher is not started: {self.__name}")
        self.__futures.append(self.__executor.submit(self.__download, addon_info))

    def wait_download_finish(self) -> None:
        log.info("Wait finish")
        if self.__executor:
            log.info("Waiting for finish")
            self.__executor.shutdown(wait=True)
            self.__executor = None
            self.__futures = []

    @abstractmethod
    def enrich(self, addon_infos: AddonInfos) -> AddonInfos:
        ...

    @abstractmethod
    def _download(self, addon_info: AddonInfo) -> None:
        ...

    @abstractmethod
    def _done(self) -> int:
        ...

    def __download(self, addon_info: AddonInfo) -> None:
        try:
            log.info(f"Enriching: {addon_info.header.id}. Done: {self._done()}")
            self._download(addon_info)
        except Exception:
            log.error(f"Error processing item: {addon_info}", exc_info=True)
            os._exit(1)
