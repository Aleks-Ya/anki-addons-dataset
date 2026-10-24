import copy
import re
from datetime import date
from itertools import groupby
from typing import Optional
from urllib.parse import urljoin

from bs4 import Tag, BeautifulSoup

from anki_addons_dataset.collector.url_parser import UrlParser
from anki_addons_dataset.collector.ankiweb.addon_branch_parser import AddonBranchParser
from anki_addons_dataset.collector.ankiweb.ai_declaration_detector import AiDeclarationDetector
from anki_addons_dataset.collector.ankiweb.description_language_detector import DescriptionLanguageDetector
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonHeader, AddonInfo, AddonId, URL, GitHubLink, GithubRepo, \
    GithubInfo, AddonPage, AddonBranch, HtmlStr, AnkiForumInfo, AddonDescription, LanguageCode, PageLink, \
    PageLinkSection, GithubRepoSource, AddonReview, ReviewVote, AnkiForumTopicSource


class AddonPageParser:
    def __init__(self, overrider: Overrider) -> None:
        self.overrider: Overrider = overrider

    def parse_addon_page(self, addon_header: AddonHeader, html: HtmlStr) -> AddonInfo:
        soup: BeautifulSoup = BeautifulSoup(html, 'html.parser')
        description_tag: Optional[Tag] = soup.find('div', class_='shared-item-description')
        anchors: list[tuple[URL, PageLinkSection, str]] = self.__extract_anchors(
            soup, description_tag, addon_header.addon_page_url)
        links: list[PageLink] = self.__fold_anchors(anchors)
        description_links: list[URL] = [url for url, section, _ in anchors if section == PageLinkSection.DESCRIPTION]
        github_links: list[GitHubLink] = UrlParser.find_github_links(description_links)
        contact_author_url: Optional[URL] = next(
            (link.url for link in links if link.section == PageLinkSection.CONTACT_AUTHOR), None)
        github_repo: Optional[GithubRepo]
        github_repo_source: Optional[GithubRepoSource]
        github_repo, github_repo_source = self.__decided_github_repo(addon_header.id, contact_author_url)
        anki_forum_links: list[URL] = UrlParser.find_anki_forum_links(description_links)
        anki_forum_url: Optional[URL]
        anki_forum_source: Optional[AnkiForumTopicSource]
        anki_forum_url, anki_forum_source = self.__deduce_anki_forum_url(
            addon_header.id, anki_forum_links, contact_author_url)
        github_info: GithubInfo = GithubInfo(github_links, github_repo, [], 0, None, 0, 0,
                                             repo_source=github_repo_source)
        likes: int = self.__extract_likes(soup)
        dislikes: int = self.__extract_dislikes(soup)
        addon_branches: list[AddonBranch] = self.__extract_addon_branches(soup)
        description: AddonDescription = self.__extract_description(description_tag)
        ai_declaration_markers: list[str] = AiDeclarationDetector.detect(description)
        description_language: Optional[LanguageCode]
        description_language_confidence: Optional[float]
        description_language, description_language_confidence = DescriptionLanguageDetector.detect(description)
        description_html: Optional[HtmlStr] = self.__extract_description_html(
            description_tag, addon_header.addon_page_url)
        description_pre_wrap: bool = self.__extract_description_pre_wrap(description_tag)
        other_items_count: int = self.__extract_other_items_count(soup)
        reviews: list[AddonReview] = self.__extract_reviews(soup)
        package_size_kb: Optional[int] = self.__extract_package_size_kb(soup)
        addon_page: AddonPage = AddonPage(
            html, likes, dislikes, addon_branches, links, description, ai_declaration_markers, description_language,
            description_language_confidence, description_html, description_pre_wrap, other_items_count, reviews,
            package_size_kb=package_size_kb)
        anki_forum_info: AnkiForumInfo = AnkiForumInfo(anki_forum_url, None, None, None, None,
                                                       topic_source=anki_forum_source)
        addon_info: AddonInfo = AddonInfo(addon_header, addon_page, github_info, anki_forum_info)
        return addon_info

    def __decided_github_repo(self, addon_id: AddonId, contact_author_url: Optional[URL]
                              ) -> tuple[Optional[GithubRepo], Optional[GithubRepoSource]]:
        override_link: Optional[GitHubLink] = self.overrider.override_github_link(addon_id)
        if override_link:
            return override_link.repo, GithubRepoSource.OVERRIDE
        contact_repo: Optional[GithubRepo] = self.__contact_author_github_repo(contact_author_url)
        if contact_repo is not None:
            return contact_repo, GithubRepoSource.CONTACT_AUTHOR
        return None, None

    def __deduce_anki_forum_url(self, addon_id: AddonId, anki_forum_urls: list[URL],
                                contact_author_url: Optional[URL]
                                ) -> tuple[Optional[URL], Optional[AnkiForumTopicSource]]:
        override_url: Optional[URL] = self.overrider.override_anki_forum_url(addon_id)
        if override_url:
            return override_url, AnkiForumTopicSource.OVERRIDE
        if contact_author_url is not None:
            contact_forum_urls: list[URL] = UrlParser.find_anki_forum_links([contact_author_url])
            if contact_forum_urls:
                return contact_forum_urls[0], AnkiForumTopicSource.CONTACT_AUTHOR
        urls_sorted: list[URL] = list(anki_forum_urls)
        urls_sorted.sort()
        grouped: groupby[URL, URL] = groupby(urls_sorted)
        counts: dict[URL, int] = {k: len(list(v)) for k, v in grouped}
        if len(counts) == 0:
            return None, None
        max_tuple: tuple[URL, int] = max(counts.items(), key=lambda item: item[1])
        return max_tuple[0], AnkiForumTopicSource.MOST_LINKED

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
    def __extract_anchors(soup: BeautifulSoup, description_tag: Optional[Tag],
                          page_url: URL) -> list[tuple[URL, PageLinkSection, str]]:
        tags: list[tuple[Tag, PageLinkSection]] = []
        if description_tag is not None:
            tags.extend((anchor, PageLinkSection.DESCRIPTION) for anchor in description_tag.find_all('a'))
        contact_author_anchor: Optional[Tag] = AddonPageParser.__find_contact_author_anchor(soup)
        if contact_author_anchor is not None:
            tags.append((contact_author_anchor, PageLinkSection.CONTACT_AUTHOR))
        anchors: list[tuple[URL, PageLinkSection, str]] = []
        for tag, section in tags:
            href: Optional[str] = tag.get('href')
            if not href:
                continue
            url: URL = URL(urljoin(page_url, href.strip()))
            if url.startswith(('http://', 'https://')):
                anchors.append((url, section, AddonPageParser.__anchor_text(tag)))
        return anchors

    @staticmethod
    def __fold_anchors(anchors: list[tuple[URL, PageLinkSection, str]]) -> list[PageLink]:
        links: dict[tuple[URL, PageLinkSection], PageLink] = {}
        for url, section, text in anchors:
            link: PageLink = links.setdefault((url, section), PageLink(url, section, 0, []))
            link.count += 1
            if text and text not in link.texts:
                link.texts.append(text)
        return list(links.values())

    @staticmethod
    def __anchor_text(anchor: Tag) -> str:
        text: str = " ".join(anchor.get_text(separator=' ', strip=True).split())
        if text:
            return text
        image: Optional[Tag] = anchor.find('img')
        if image is not None:
            return " ".join(str(image.get('alt', '')).split())
        return ""

    @staticmethod
    def __find_contact_author_anchor(soup: BeautifulSoup) -> Optional[Tag]:
        for anchor in soup.find_all('a'):
            if anchor.get_text(strip=True) == 'Contact Author' and anchor.get('href'):
                return anchor
        return None

    @staticmethod
    def __extract_other_items_count(soup: BeautifulSoup) -> int:
        by_author_anchor: Optional[Tag] = soup.find('a', href=re.compile(r'^/shared/by-author/'))
        if by_author_anchor is None:
            return 0
        match: Optional[re.Match[str]] = re.search(r'\d+', by_author_anchor.get_text())
        return int(match.group()) if match else 0

    @staticmethod
    def __extract_package_size_kb(soup: BeautifulSoup) -> Optional[int]:
        size_pattern: re.Pattern[str] = re.compile(r'^\s*(?:<(\d+)kB|(\d+(?:\.\d+)?)MB)\. Updated')
        for small_tag in soup.find_all('small'):
            match: Optional[re.Match[str]] = size_pattern.match(small_tag.get_text())
            if match:
                return 0 if match.group(1) else round(float(match.group(2)) * 1000)
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
    def __extract_reviews(soup: BeautifulSoup) -> list[AddonReview]:
        reviews_heading: Optional[Tag] = soup.find('h2', string='Reviews')
        if reviews_heading is None:
            return []
        reviews: list[AddonReview] = []
        for vote_image in reviews_heading.find_all_next('img', alt=[vote.value for vote in ReviewVote]):
            header: Tag = vote_image.parent
            timestamp: Tag = header.find('span', class_='timestamp')
            body: Optional[Tag] = header.find_next_sibling('div')
            text_tag: Optional[Tag] = body.find('div', class_='break-word', recursive=False) if body else None
            reply_tag: Optional[Tag] = body.find('div', class_='card-body') if body else None
            reviews.append(AddonReview(
                ReviewVote(vote_image['alt']),
                date.fromisoformat(timestamp.get_text(strip=True)),
                text_tag.get_text().strip() if text_tag else "",
                reply_tag.get_text().strip() if reply_tag else None))
        return reviews

    @staticmethod
    def __extract_description(description_tag: Optional[Tag]) -> AddonDescription:
        if description_tag is None:
            return AddonDescription("")
        return AddonDescription(" ".join(description_tag.get_text(separator=' ', strip=True).split()))

    @staticmethod
    def __extract_description_html(description_tag: Optional[Tag], page_url: URL) -> Optional[HtmlStr]:
        if description_tag is None:
            return None
        description_copy: Tag = copy.copy(description_tag)
        for attribute in ('href', 'src'):
            for tag in description_copy.find_all(attrs={attribute: True}):
                tag[attribute] = AddonPageParser.__absolute_url(page_url, str(tag[attribute]))
        for tag in description_copy.find_all(srcset=True):
            tag['srcset'] = AddonPageParser.__absolute_srcset(page_url, str(tag['srcset']))
        description_html: HtmlStr = HtmlStr(description_copy.decode_contents())
        return description_html if description_html.strip() else None

    @staticmethod
    def __absolute_url(page_url: URL, url: str) -> URL:
        stripped: str = url.strip()
        if not stripped or stripped.startswith('#'):
            return URL(url)
        return URL(urljoin(page_url, stripped))

    @staticmethod
    def __absolute_srcset(page_url: URL, srcset: str) -> str:
        candidates: list[str] = []
        for candidate in re.split(r',\s+', srcset.strip()):
            parts: list[str] = candidate.split()
            if parts:
                parts[0] = AddonPageParser.__absolute_url(page_url, parts[0])
                candidates.append(" ".join(parts))
        return ", ".join(candidates)

    @staticmethod
    def __extract_description_pre_wrap(description_tag: Optional[Tag]) -> bool:
        if description_tag is None:
            return False
        return 'pre-wrap' in (description_tag.get('class') or [])

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
