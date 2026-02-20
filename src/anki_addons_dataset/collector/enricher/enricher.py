from datetime import datetime
from pathlib import Path
from queue import Queue
from threading import Thread
from typing import Optional
import logging
from logging import Logger

from anki_addons_dataset.common.data_types import AddonInfo, LanguageName, GithubInfo, AddonHeader, AddonPage, AddonId, \
    AddonInfos
from anki_addons_dataset.collector.github.github_service import GithubService
from anki_addons_dataset.common.json_helper import JsonHelper
from anki_addons_dataset.common.working_dir import VersionDir

log: Logger = logging.getLogger(__name__)


class Enricher(Thread):
    def __init__(self, version_dir: VersionDir, github_service: GithubService):
        super().__init__(daemon=True)
        self.__stage_dir: Path = version_dir.get_stage_dir() / "3-enricher" / "addon"
        self.__github_service: GithubService = github_service
        self.__queue: Queue[AddonInfo] = Queue()
        self.__github_infos: dict[AddonId, GithubInfo] = {}
        self.__sentinel: AddonInfo = AddonInfo(AddonHeader(AddonId(0), "", "", 0, "", ""),
                                               AddonPage(0, 0, [], [], None), None)

    def run(self) -> None:
        while True:
            item: AddonInfo = self.__queue.get()
            if item is self.__sentinel:
                log.info("Finishing by sentinel")
                self.__queue.task_done()
                break
            try:
                self.__download(item)
            except Exception as e:
                raise RuntimeError(f"Error processing item: {item}", e)
            self.__queue.task_done()
        log.info("Exit run")

    def download_in_background(self, addon_info: AddonInfo) -> None:
        log.info(f"Enqueue for enriching: {addon_info.header.id}")
        self.__queue.put(addon_info)

    def wait_download_finish(self) -> None:
        log.info("Wait finish")
        if self.is_alive():
            log.info("Waiting for finish")
            self.__queue.put(self.__sentinel)
            self.__queue.join()

    def enrich(self, addon_infos: AddonInfos) -> AddonInfos:
        return AddonInfos([self.__enrich(addon_info, self.__github_infos[addon_info.header.id])
                           for addon_info in addon_infos])

    def __download(self, addon_info: AddonInfo) -> None:
        log.info(f"Enriching: {addon_info.header.id}. Queue: {self.__queue.qsize()}. "
                 f"Done: {len(self.__github_infos)}")
        languages: list[LanguageName] = self.__get_languages(addon_info)
        stars: int = self.__github_service.get_stars_count(addon_info.github.github_repo)
        last_commit: Optional[datetime] = self.__github_service.get_last_commit(addon_info.github.github_repo)
        action_count: int = self.__github_service.get_action_count(addon_info.github.github_repo)
        tests_count: int = self.__github_service.get_tests_count(addon_info.github.github_repo)
        github_info: GithubInfo = GithubInfo(addon_info.github.github_links, addon_info.github.github_repo,
                                             languages, stars, last_commit, action_count, tests_count)
        self.__github_infos[addon_info.header.id] = github_info

    def __get_languages(self, addon_info: AddonInfo) -> list[LanguageName]:
        if addon_info.github.github_repo:
            language_dict: dict[LanguageName, int] = self.__github_service.get_languages(
                addon_info.github.github_repo)
            languages: list[LanguageName] = list(language_dict.keys())
        else:
            languages: list[LanguageName] = []
        return languages

    def __enrich(self, addon_info: AddonInfo, github_info: GithubInfo) -> AddonInfo:
        enriched_addon_info: AddonInfo = AddonInfo(addon_info.header, addon_info.page, github_info)
        addon_json_file: Path = self.__stage_dir / f"{addon_info.header.id}.json"
        JsonHelper.write_addon_info_to_file(addon_info, addon_json_file)
        log.info(f"Enriched: {addon_info.header.id}")
        return enriched_addon_info
