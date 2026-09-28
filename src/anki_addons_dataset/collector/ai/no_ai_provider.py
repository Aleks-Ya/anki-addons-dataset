from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText


class NoAiProvider(AiProvider):

    def response(self, prompt: AiPrompt) -> Optional[AiResponseText]:
        raise AssertionError("NoAiProvider must not be called")

    def verify_access(self) -> Optional[str]:
        raise AssertionError("NoAiProvider must not be called")
