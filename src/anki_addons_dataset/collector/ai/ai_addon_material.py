from textwrap import dedent
from typing import Optional

from anki_addons_dataset.common.data_types import AddonTitle, AddonDescription, GithubReadme


class AiAddonMaterial:

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
                                description=description or 'No description provided.',
                                readme=self.truncate(readme) or 'No README provided.')

    def truncate(self, readme: Optional[GithubReadme]) -> Optional[GithubReadme]:
        """READMEs run to tens of kilobytes, and the prompts rarely need more than the opening."""
        if readme is None or len(readme) <= self.__readme_max_chars:
            return readme
        return GithubReadme(f"{readme[:self.__readme_max_chars]}\n\n(README truncated.)")
