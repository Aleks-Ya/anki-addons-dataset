import logging
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.ai.ai_summarizer import AiSummarizer
from anki_addons_dataset.collector.enricher import Enricher
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AiInfo, AiModel, AiSummary, \
    GithubReadme

log: Logger = logging.getLogger(__name__)


class AiEnricher(Enricher):
    __name: str = "Ai"

    def __init__(self, ai_summarizer: AiSummarizer, model: AiModel):
        super().__init__(name=self.__name)
        self.__ai_summarizer: AiSummarizer = ai_summarizer
        self.__model: AiModel = model
        self.__summaries: dict[AddonId, Optional[AiSummary]] = {}

    def enrich(self, addon_infos: AddonInfos) -> AddonInfos:
        return AddonInfos([self.__enrich(addon_info, self.__summaries[addon_info.header.id])
                           for addon_info in addon_infos])

    def _download(self, addon_info: AddonInfo) -> None:
        readme: Optional[GithubReadme] = addon_info.github.readme if addon_info.github else None
        try:
            summary: Optional[AiSummary] = self.__ai_summarizer.summarize(
                addon_info.header.title, addon_info.page.description, readme)
        except Exception as e:
            raise RuntimeError(f"Cannot summarize addon: {addon_info.header.id}") from e
        self.__summaries[addon_info.header.id] = summary

    def _done(self) -> int:
        return len(self.__summaries)

    def __enrich(self, addon_info: AddonInfo, summary: Optional[AiSummary]) -> AddonInfo:
        if summary is None:
            return addon_info
        return AddonInfo(addon_info.header, addon_info.page, addon_info.github, addon_info.forum,
                         AiInfo(summary, self.__model))
