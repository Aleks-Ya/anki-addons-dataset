import logging
from concurrent.futures import ThreadPoolExecutor
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.ai.ai_summarizer import AiSummarizer
from anki_addons_dataset.common.data_types import AddonInfo, AddonInfos, AiInfo, AiModel, AiSummary, GithubReadme

log: Logger = logging.getLogger(__name__)


class AiEnricher:
    """Adds the AI summary to already-enriched AddonInfos.

    Deliberately not an Enricher: the prompt needs the GitHub README, so this runs after the
    GitHub and forum enrichers have finished rather than in parallel with them."""

    def __init__(self, ai_summarizer: AiSummarizer, model: AiModel, workers: int):
        self.__ai_summarizer: AiSummarizer = ai_summarizer
        self.__model: AiModel = model
        self.__workers: int = workers

    def enrich(self, addon_infos: AddonInfos) -> AddonInfos:
        log.info(f"Summarizing {len(addon_infos)} addons in {self.__workers} threads")
        with ThreadPoolExecutor(max_workers=self.__workers, thread_name_prefix="Ai") as executor:
            summaries: list[Optional[AiSummary]] = list(executor.map(self.__summarize, addon_infos))
        return AddonInfos([self.__enrich(addon_info, summary)
                           for addon_info, summary in zip(addon_infos, summaries)])

    def __summarize(self, addon_info: AddonInfo) -> Optional[AiSummary]:
        readme: Optional[GithubReadme] = addon_info.github.readme if addon_info.github else None
        return self.__ai_summarizer.summarize(addon_info.header.title, addon_info.page.description, readme)

    def __enrich(self, addon_info: AddonInfo, summary: Optional[AiSummary]) -> AddonInfo:
        if summary is None:
            return addon_info
        return AddonInfo(addon_info.header, addon_info.page, addon_info.github, addon_info.forum,
                         AiInfo(summary, self.__model))
