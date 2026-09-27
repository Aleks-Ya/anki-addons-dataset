from typing import Optional

from anki_addons_dataset.collector.ai.ai_provider import AiProvider, AiPrompt, AiResponseText


class NoAiProvider(AiProvider):
    """Stands in for a real provider where no request may be made, so that PARSE needs no API key.

    CachedAiProvider in offline mode answers from the cache or returns None, never reaching here."""

    def response(self, prompt: AiPrompt) -> Optional[AiResponseText]:
        raise AssertionError("NoAiProvider must not be called")
