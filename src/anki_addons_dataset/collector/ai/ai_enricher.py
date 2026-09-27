import logging
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.ai.ai_summarizer import AiSummarizer
from anki_addons_dataset.common.data_types import AddonInfo, AddonInfos, AiInfo, AiModel, AiSummary, GithubReadme

log: Logger = logging.getLogger(__name__)


class AiEnricher:
    def __init__(self, ai_summarizer: AiSummarizer, model: AiModel):
        self.__ai_summarizer: AiSummarizer = ai_summarizer
        self.__model: AiModel = model

    def enrich(self, addon_infos: AddonInfos) -> AddonInfos:
        log.info(f"Summarizing {len(addon_infos)} addons")
        return AddonInfos([self.__enrich(addon_info, self.__summarize(addon_info)) for addon_info in addon_infos])

    def __summarize(self, addon_info: AddonInfo) -> Optional[AiSummary]:
        readme: Optional[GithubReadme] = addon_info.github.readme if addon_info.github else None
        try:
            return self.__ai_summarizer.summarize(addon_info.header.title, addon_info.page.description, readme)
        except Exception as e:
            raise RuntimeError(f"Cannot summarize addon: {addon_info.header.id}") from e

    def __enrich(self, addon_info: AddonInfo, summary: Optional[AiSummary]) -> AddonInfo:
        if summary is None:
            return addon_info
        return AddonInfo(addon_info.header, addon_info.page, addon_info.github, addon_info.forum,
                         AiInfo(summary, self.__model))
