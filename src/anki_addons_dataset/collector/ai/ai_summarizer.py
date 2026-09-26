import logging
from logging import Logger
from textwrap import dedent
from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText
from anki_addons_dataset.common.data_types import AddonTitle, AddonDescription, GithubReadme, AiSummary

log: Logger = logging.getLogger(__name__)


class AiSummarizer:

    def __init__(self, ai_provider: AiProvider):
        self.__ai_provider: AiProvider = ai_provider

    def summarize(self, title: AddonTitle, addon_description: AddonDescription,
                  github_readme: Optional[GithubReadme]) -> Optional[AiSummary]:
        prompt: AiPrompt = AiPrompt(dedent(f"""
            You need to prepare a summary of an addon for the Anki flashcard application according to the guidelines.
            
            <addon_title>
            {title}
            </addon_title>
            
            <addon_description>
            {addon_description}
            </addon_description>
            
            <addon_github_readme>
            {github_readme if github_readme else 'No README provided.'}
            </addon_github_readme>
            
            <guidelines>
                <guideline>Summary should contain a single sentence.</guideline>
                <guideline>Summary should not repeat the addon name.</guideline>
                <guideline>Start directly with what the addon does, omitting introductory prefixes such as "This Anki add-on".</guideline>
            </guidelines>
            """))
        ai_response: Optional[AiResponseText] = self.__ai_provider.response(prompt)
        return AiSummary(ai_response) if ai_response is not None else None
