from textwrap import dedent
from typing import Callable, Optional

from anki_addons_dataset.collector.ai.provider.ai_provider import AiResponseText
from anki_addons_dataset.common.data_types import AddonTitle, AddonDescription, AddonInfo, GithubReadme


class AiAddonMaterial:
    no_description: str = "No description provided."
    no_readme: str = "No README provided."
    missing_value: str = "None."

    def __init__(self, readme_max_chars: int):
        self.__readme_max_chars: int = readme_max_chars

    def format(self, title: AddonTitle, description: AddonDescription, readme: Optional[GithubReadme]) -> str:
        return dedent("""
            <addon_title>
            {title}
            </addon_title>

            <addon_description>
            {description}
            </addon_description>

            <addon_github_readme>
            {readme}
            </addon_github_readme>
            """).strip().format(title=title,
                                description=description or self.no_description,
                                readme=self.truncate(readme) or self.no_readme)

    def truncate(self, readme: Optional[GithubReadme]) -> Optional[GithubReadme]:
        """READMEs run to tens of kilobytes, and the prompts rarely need more than the opening."""
        if readme is None or len(readme) <= self.__readme_max_chars:
            return readme
        return GithubReadme(f"{readme[:self.__readme_max_chars]}\n\n(README truncated.)")

    @staticmethod
    def normalize_answer(ai_response: AiResponseText) -> str:
        return ai_response.strip().strip("`'\".").strip().lower()

    @staticmethod
    def link_texts(addon_info: AddonInfo, matches: Callable[[str], bool]) -> list[str]:
        texts: list[str] = []
        for link in addon_info.page.links:
            if matches(link.url):
                texts.extend(text for text in link.texts if text not in texts)
        return texts
