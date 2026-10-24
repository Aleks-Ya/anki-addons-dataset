from typing import Optional

from anki_addons_dataset.collector.ai.provider.ai_provider import AiProvider, AiPrompt, AiResponseText, AiInstructions


class NoAiProvider(AiProvider):

    def response(self, prompt: AiPrompt, instructions: Optional[AiInstructions] = None) -> Optional[AiResponseText]:
        raise AssertionError("NoAiProvider must not be called")

    def verify_access(self) -> Optional[str]:
        raise AssertionError("NoAiProvider must not be called")
