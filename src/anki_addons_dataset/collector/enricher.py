import os
from abc import ABC, abstractmethod
from queue import Queue
from threading import Thread
import logging
from logging import Logger

from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonPage, AddonId, \
    AddonInfos

log: Logger = logging.getLogger(__name__)


class Enricher(ABC, Thread):

    def __init__(self, name: str):
        super().__init__(name=name, daemon=True)
        self.__name: str = name
        self.__queue: Queue[AddonInfo] = Queue()
        self.__sentinel: AddonInfo = AddonInfo(AddonHeader(AddonId(0), "", "", 0, "", ""),
                                               AddonPage(0, 0, [], [], None), None, None)

    def run(self) -> None:
        log.info(f"Start thread: {self.__name}")
        while True:
            item: AddonInfo = self.__queue.get()
            if item is self.__sentinel:
                log.info("Finishing by sentinel")
                self.__queue.task_done()
                break
            try:
                log.info(f"Enriching: {item.header.id}. Queue: {self.__queue.qsize()}. Done: {self._done()}")
                self._download(item)
            except Exception:
                log.error(f"Error processing item: {item}", exc_info=True)
                os._exit(1)
            self.__queue.task_done()
        log.info("Exit run")

    def download_in_background(self, addon_info: AddonInfo) -> None:
        log.info(f"Enqueue for enriching ({self.__name}): {addon_info.header.id}")
        self.__queue.put(addon_info)

    def wait_download_finish(self) -> None:
        log.info("Wait finish")
        if self.is_alive():
            log.info("Waiting for finish")
            self.__queue.put(self.__sentinel)
            self.__queue.join()

    @abstractmethod
    def enrich(self, addon_infos: AddonInfos) -> AddonInfos:
        ...

    @abstractmethod
    def _download(self, addon_info: AddonInfo) -> None:
        ...

    @abstractmethod
    def _done(self) -> int:
        ...
