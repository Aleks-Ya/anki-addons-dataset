import re
from re import Match
from typing import Optional

from anki_addons_dataset.common.data_types import URL, GithubLink, GithubRepo, GithubRepoName, GithubUserName, \
    GithubUser


class UrlParser:

    @staticmethod
    def find_github_links(links: list[URL]) -> list[GithubLink]:
        parsed_links: list[Optional[GithubLink]] = [UrlParser.parse_github_url(URL(link)) for link in links]
        return [link for link in parsed_links if link is not None]

    @staticmethod
    def find_anki_forum_links(links: list[URL]) -> list[URL]:
        parsed_links: list[Optional[URL]] = [UrlParser.__parse_anki_forum_url(URL(link)) for link in links]
        return [link for link in parsed_links if link is not None]

    @staticmethod
    def parse_github_url(url: URL) -> Optional[GithubLink]:
        repo_pattern: str = r'https://github\.com[:/](?P<user>[^/]+)/(?P<repo>[^/?#)(]+)'
        repo_match: Optional[Match[str]] = re.search(repo_pattern, url)
        if repo_match:
            user_name: GithubUserName = GithubUserName(repo_match.group('user').lower())
            user: GithubUser = GithubUser(user_name)
            repo_name: GithubRepoName = GithubRepoName(repo_match.group('repo').lower())
            repo: GithubRepo = GithubRepo(user_name, repo_name)
            return GithubLink(url, user, repo)
        user_pattern: str = r'https://github\.com[:/](?P<user>[^/]+)'
        user_match: Optional[Match[str]] = re.search(user_pattern, url)
        if user_match:
            owner: GithubUser = GithubUser(GithubUserName(user_match.group('user')))
            return GithubLink(url, owner, None)
        return None

    @staticmethod
    def __parse_anki_forum_url(url: URL) -> Optional[URL]:
        pattern: str = r"https://forums\.ankiweb\.net/t/[\w\-]+/\d+"
        match: Optional[Match[str]] = re.match(pattern, url)
        return url if match else None
