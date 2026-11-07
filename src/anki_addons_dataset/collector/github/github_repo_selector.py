import copy
import logging
import re
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.ai.question.ai_repo_selector import AiRepoSelector, AiRepoAnswer
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.collector.url_parser import UrlParser
from anki_addons_dataset.common.data_types import AddonInfo, AddonId, GithubInfo, GithubRepo, GithubRepoSource, \
    GithubLink, URL

log: Logger = logging.getLogger(__name__)


class GithubRepoSelector:

    def __init__(self, overrider: Overrider, ai_repo_selector: Optional[AiRepoSelector]):
        self.__overrider: Overrider = overrider
        self.__ai_repo_selector: Optional[AiRepoSelector] = ai_repo_selector

    def decided_repo(self, addon_info: AddonInfo) -> Optional[tuple[GithubRepo, GithubRepoSource]]:
        override_link: Optional[GithubLink] = self.__overrider.override_github_link(addon_info.header.id)
        if override_link:
            return (override_link.repo, GithubRepoSource.OVERRIDE) if override_link.repo is not None else None
        contact_repo: Optional[GithubRepo] = self.__contact_author_repo(addon_info.page.contact_author_url)
        return (contact_repo, GithubRepoSource.CONTACT_AUTHOR) if contact_repo is not None else None

    def candidate_repos(self, github_links: list[GithubLink]) -> list[GithubRepo]:
        return list(dict.fromkeys(self.__allowed_repos(github_links)))

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

    def __contact_author_repo(self, contact_author_url: Optional[URL]) -> Optional[GithubRepo]:
        if contact_author_url is None:
            return None
        allowed_repos: list[GithubRepo] = self.__allowed_repos(UrlParser.find_github_links([contact_author_url]))
        return allowed_repos[0] if allowed_repos else None

    def __allowed_repos(self, github_links: list[GithubLink]) -> list[GithubRepo]:
        return [link.repo for link in github_links
                if link.repo is not None and not self.__overrider.is_excluded_github_repo(link.url)]

    @staticmethod
    def __references_addon(candidate: GithubInfo, addon_id: AddonId) -> bool:
        id_pattern: re.Pattern[str] = re.compile(rf"(?<!\d){addon_id}(?!\d)")
        texts: list[Optional[str]] = [candidate.readme, candidate.homepage, candidate.repo_description,
                                      candidate.manifest.homepage if candidate.manifest else None]
        return any(text is not None and id_pattern.search(text) for text in texts)

    @staticmethod
    def __most_linked(addon_info: AddonInfo, candidates: list[GithubInfo]) -> GithubInfo:
        link_repos: list[Optional[GithubRepo]] = [link.repo for link in addon_info.page.github_links]
        return max(sorted(candidates, key=lambda candidate: candidate.github_repo.get_id()),
                   key=lambda candidate: link_repos.count(candidate.github_repo))

    @staticmethod
    def __with_source(github_info: GithubInfo, repo_source: GithubRepoSource) -> GithubInfo:
        log.debug(f"Selected GitHub repo {github_info.github_repo.get_id()} by {repo_source}")
        return copy.replace(github_info, repo_source=repo_source)
