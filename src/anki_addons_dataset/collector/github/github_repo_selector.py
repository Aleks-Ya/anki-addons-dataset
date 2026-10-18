import dataclasses
import logging
import re
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.ai.ai_repo_selector import AiRepoSelector, AiRepoAnswer
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonInfo, AddonId, GithubInfo, GithubRepo, GithubRepoSource, \
    GitHubLink

log: Logger = logging.getLogger(__name__)


class GithubRepoSelector:

    def __init__(self, overrider: Overrider, ai_repo_selector: Optional[AiRepoSelector]):
        self.__overrider: Overrider = overrider
        self.__ai_repo_selector: Optional[AiRepoSelector] = ai_repo_selector

    def candidate_repos(self, github_links: list[GitHubLink]) -> list[GithubRepo]:
        allowed_links: list[GitHubLink] = [link for link in github_links if link.repo is not None
                                           and not self.__overrider.is_excluded_github_repo(link.url)]
        return list(dict.fromkeys(link.repo for link in allowed_links))

    def select(self, addon_info: AddonInfo, candidates: list[GithubInfo]) -> Optional[GithubInfo]:
        if not candidates:
            return None
        self_referencing: list[GithubInfo] = [candidate for candidate in candidates
                                              if self.__references_addon(candidate, addon_info.header.id)]
        if len(self_referencing) == 1:
            return self.__with_source(self_referencing[0], GithubRepoSource.SELF_REFERENCE)
        if self.__ai_repo_selector is not None:
            answer: Optional[AiRepoAnswer] = self.__ai_repo_selector.select(addon_info, candidates)
            if answer is not None:
                chosen: Optional[GithubInfo] = next(
                    (candidate for candidate in candidates if candidate.github_repo == answer.repo), None)
                return self.__with_source(chosen, GithubRepoSource.AI) if chosen is not None else None
        return self.__with_source(self.__most_linked(addon_info, candidates), GithubRepoSource.MOST_LINKED)

    @staticmethod
    def __references_addon(candidate: GithubInfo, addon_id: AddonId) -> bool:
        id_pattern: re.Pattern[str] = re.compile(rf"(?<!\d){addon_id}(?!\d)")
        texts: list[Optional[str]] = [candidate.readme, candidate.homepage, candidate.repo_description,
                                      candidate.manifest.homepage if candidate.manifest else None]
        return any(text is not None and id_pattern.search(text) for text in texts)

    @staticmethod
    def __most_linked(addon_info: AddonInfo, candidates: list[GithubInfo]) -> GithubInfo:
        link_repos: list[Optional[GithubRepo]] = [link.repo for link in addon_info.github.github_links]
        return max(sorted(candidates, key=lambda candidate: candidate.github_repo.get_id()),
                   key=lambda candidate: link_repos.count(candidate.github_repo))

    @staticmethod
    def __with_source(github_info: GithubInfo, repo_source: GithubRepoSource) -> GithubInfo:
        log.debug(f"Selected GitHub repo {github_info.github_repo.get_id()} by {repo_source}")
        return dataclasses.replace(github_info, repo_source=repo_source)
