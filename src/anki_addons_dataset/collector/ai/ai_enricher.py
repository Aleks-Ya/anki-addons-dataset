import copy
import logging
from logging import Logger
from threading import Lock
from typing import Optional

from anki_addons_dataset.collector.ai.ai_summarizer import AiSummarizer
from anki_addons_dataset.collector.ai.ai_tagger import AiTagger
from anki_addons_dataset.collector.enricher import Enricher
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AiInfo, AiModel, AiSummary, \
    AiTag, GithubReadme

log: Logger = logging.getLogger(__name__)


class AiEnricher(Enricher):
    __name: str = "Ai"
    __pool_size: int = 50

    def __init__(self, ai_summarizer: AiSummarizer, ai_tagger: AiTagger, model: AiModel):
        super().__init__(name=self.__name, pool_size=self.__pool_size)
        self.__ai_summarizer: AiSummarizer = ai_summarizer
        self.__ai_tagger: AiTagger = ai_tagger
        self.__model: AiModel = model
        self.__results: dict[AddonId, tuple[Optional[AiSummary], Optional[list[AiTag]]]] = {}
        self.__lock: Lock = Lock()

    def enrich(self, addon_infos: AddonInfos) -> AddonInfos:
        return AddonInfos([self.__enrich(addon_info, *self.__results[addon_info.header.id])
                           for addon_info in addon_infos])

    def _download(self, addon_info: AddonInfo) -> None:
        readme: Optional[GithubReadme] = addon_info.github.readme if addon_info.github else None
        try:
            summary: Optional[AiSummary] = self.__ai_summarizer.summarize(
                addon_info.header.title, addon_info.page.description, readme)
        except Exception as e:
            raise RuntimeError(f"Cannot summarize addon: {addon_info.header.id}") from e
        try:
            tags: Optional[list[AiTag]] = self.__ai_tagger.tag(
                addon_info.header.title, addon_info.page.description, readme)
        except Exception as e:
            raise RuntimeError(f"Cannot tag addon: {addon_info.header.id}") from e
        with self.__lock:
            self.__results[addon_info.header.id] = (summary, tags)

    def _done(self) -> int:
        with self.__lock:
            return len(self.__results)

    def __enrich(self, addon_info: AddonInfo, summary: Optional[AiSummary],
                 tags: Optional[list[AiTag]]) -> AddonInfo:
        if summary is None and tags is None:
            return addon_info
        return copy.replace(addon_info, ai=AiInfo(summary, self.__model, tags))
