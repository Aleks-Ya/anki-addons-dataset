from itertools import groupby
from typing import Optional

from bs4 import Tag, BeautifulSoup

from anki_addons_dataset.collector.url_parser import UrlParser
from anki_addons_dataset.collector.ankiweb.addon_branch_parser import AddonBranchParser
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonHeader, AddonInfo, AddonId, URL, GitHubLink, GithubRepo, \
    GithubInfo, AddonPage, AddonBranch, HtmlStr, AnkiForumInfo


class AddonPageParser:
    def __init__(self, overrider: Overrider) -> None:
        self.overrider: Overrider = overrider

    def parse_addon_page(self, addon_header: AddonHeader, html: HtmlStr) -> AddonInfo:
        soup: BeautifulSoup = BeautifulSoup(html, 'html.parser')
        description_tag: Optional[Tag] = soup.find('div', class_='shared-item-description')
        all_links: list[URL] = UrlParser.extract_all_links(html)
        description_links: list[URL] = (
            UrlParser.extract_all_links(HtmlStr(str(description_tag))) if description_tag is not None else [])
        github_links: list[GitHubLink] = UrlParser.find_github_links(description_links)
        other_links: list[URL] = [link for link in all_links if link not in github_links]
        contact_author_url: Optional[URL] = self.__extract_contact_author_url(soup)
        github_repo: Optional[GithubRepo] = self.__deduct_github_repo_name(
            addon_header.id, github_links, contact_author_url)
        anki_forum_links: list[URL] = UrlParser.find_anki_forum_links(description_links)
        anki_forum_url: Optional[URL] = self.__deduct_anki_forum_url(
            addon_header.id, anki_forum_links, contact_author_url)
        github_info: GithubInfo = GithubInfo(github_links, github_repo, [], 0, None, 0, 0)
        likes: int = self.__extract_likes(soup)
        dislikes: int = self.__extract_dislikes(soup)
        addon_branches: list[AddonBranch] = self.__extract_addon_branches(soup)
        description: str = self.__extract_description(description_tag)
        addon_page: AddonPage = AddonPage(
            html, likes, dislikes, addon_branches, other_links, description, contact_author_url)
        anki_forum_info: AnkiForumInfo = AnkiForumInfo(anki_forum_url, None, None, None, None)
        addon_info: AddonInfo = AddonInfo(addon_header, addon_page, github_info, anki_forum_info)
        return addon_info

    def __deduct_github_repo_name(self, addon_id: AddonId, github_urls: list[GitHubLink],
                                  contact_author_url: Optional[URL]) -> Optional[GithubRepo]:
        override_link: Optional[GitHubLink] = self.overrider.override_github_link(addon_id)
        if override_link:
            return override_link.repo
        contact_repo: Optional[GithubRepo] = self.__contact_author_github_repo(contact_author_url)
        if contact_repo is not None:
            return contact_repo
        not_null_urls: list[GitHubLink] = [link for link in github_urls if link.repo is not None]
        filtered_urls: list[GitHubLink] = self.__exclude_links(not_null_urls)
        filtered_urls.sort(key=lambda link: link.repo.get_id())
        grouped: groupby[GithubRepo, GitHubLink] = groupby(filtered_urls, key=lambda link: link.repo)
        counts: dict[GithubRepo, int] = {k: len(list(v)) for k, v in grouped}
        if len(counts) == 0:
            return None
        max_tuple: tuple[GithubRepo, int] = max(counts.items(), key=lambda item: item[1])
        github_repo: GithubRepo = max_tuple[0]
        return github_repo

    def __deduct_anki_forum_url(self, addon_id: AddonId, anki_forum_urls: list[URL],
                                contact_author_url: Optional[URL]) -> Optional[URL]:
        override_url: Optional[URL] = self.overrider.override_anki_forum_url(addon_id)
        if override_url:
            return override_url
        if contact_author_url is not None:
            contact_forum_urls: list[URL] = UrlParser.find_anki_forum_links([contact_author_url])
            if contact_forum_urls:
                return contact_forum_urls[0]
        urls_sorted: list[URL] = list(anki_forum_urls)
        urls_sorted.sort()
        grouped: groupby[URL, URL] = groupby(urls_sorted)
        counts: dict[URL, int] = {k: len(list(v)) for k, v in grouped}
        if len(counts) == 0:
            return None
        max_tuple: tuple[URL, int] = max(counts.items(), key=lambda item: item[1])
        return max_tuple[0]

    def __contact_author_github_repo(self, contact_author_url: Optional[URL]) -> Optional[GithubRepo]:
        if contact_author_url is None:
            return None
        contact_links: list[GitHubLink] = UrlParser.find_github_links([contact_author_url])
        allowed_links: list[GitHubLink] = self.__exclude_links(contact_links)
        for link in allowed_links:
            if link.repo is not None:
                return link.repo
        return None

    def __exclude_links(self, links: list[GitHubLink]) -> list[GitHubLink]:
        return [link for link in links if not self.overrider.is_excluded_github_repo(link.url)]

    @staticmethod
    def __extract_contact_author_url(soup: BeautifulSoup) -> Optional[URL]:
        for anchor in soup.find_all('a'):
            if anchor.get_text(strip=True) == 'Contact Author':
                href: Optional[str] = anchor.get('href')
                if href:
                    return URL(href)
        return None

    @staticmethod
    def __extract_likes(soup: BeautifulSoup) -> int:
        return AddonPageParser.__extract_vote_count(soup, 'thumbs up')

    @staticmethod
    def __extract_dislikes(soup: BeautifulSoup) -> int:
        return AddonPageParser.__extract_vote_count(soup, 'thumbs down')

    @staticmethod
    def __extract_vote_count(soup: BeautifulSoup, alt: str) -> int:
        vote_image: Optional[Tag] = soup.find('img', alt=alt)
        if vote_image is None:
            return 0
        sibling = vote_image.next_sibling
        if sibling is None:
            return 0
        return int(sibling.get_text())

    @staticmethod
    def __extract_description(description_tag: Optional[Tag]) -> str:
        if description_tag is None:
            return ""
        return " ".join(description_tag.get_text(separator=' ', strip=True).split())

    @staticmethod
    def __extract_addon_branches(soup: BeautifulSoup) -> list[AddonBranch]:
        addon_branches: list[AddonBranch] = []
        addon_branches_tag: Optional[Tag] = soup.find('ul', class_='mb-0')
        if addon_branches_tag:
            for addon_branch_tag in addon_branches_tag.find_all('li'):
                text: str = addon_branch_tag.get_text().strip()
                addon_branch: AddonBranch = AddonBranchParser.extract_addon_branch(text)
                addon_branches.append(addon_branch)
        return addon_branches
