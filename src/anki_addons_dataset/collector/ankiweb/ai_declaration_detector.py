import re
from typing import Optional, Pattern

# Explicit "the author says they built this with AI" phrasings found in the AnkiWeb addon-page
# description. Distinct from the GitHub repo-fingerprint detection in
# collector/github/handler/ai_tooling_detector.py: this reads the author's own prose, so it must
# match self-referential *build* claims and NOT feature mentions ("generate cards with ChatGPT").
#
# Supports English and Portuguese declarations via parallel, per-language pattern sets (_EN/_PT
# suffixes) rather than merging both languages' words into shared alternations -- this keeps the
# well-tested English patterns untouched and gives future languages a template to follow.

# Verbs that indicate the addon itself was built, followed (within a short window) by an AI tool.
_BUILD_DECLARATION_EN: Pattern[str] = re.compile(
    r"\b(?:built|made|created|coded|written|developed|generated)\b"
    r"[^.]{0,30}\b(?:with|using|by|via)\b"
    r"[^.]{0,20}\b(?P<tool>ai|chatgpt|gpt|claude|copilot|cursor|gemini|llm)\b",
    re.IGNORECASE,
)
_BUILD_DECLARATION_PT: Pattern[str] = re.compile(
    r"\b(?:feito|criado|codificado|escrito|desenvolvido|gerado)\b"
    r"[^.]{0,30}\b(?:com|usando|por)\b"
    r"[^.]{0,20}\b(?P<tool>ia|chatgpt|gpt|claude|copilot|cursor|gemini|llm)\b",
    re.IGNORECASE,
)
_BUILD_DECLARATIONS: list[Pattern[str]] = [_BUILD_DECLARATION_EN, _BUILD_DECLARATION_PT]

# "made with <tool>" branded phrasing; the captured tool name is normalized to a slug.
_MADE_WITH_EN: Pattern[str] = re.compile(r"\bmade with (cursor|copilot|v0|bolt\.new|lovable)\b", re.IGNORECASE)
_MADE_WITH_PT: Pattern[str] = re.compile(r"\bfeito com (cursor|copilot|v0|bolt\.new|lovable)\b", re.IGNORECASE)
_MADE_WITHS: list[Pattern[str]] = [_MADE_WITH_EN, _MADE_WITH_PT]

# Standalone provenance markers that are themselves a build declaration.
_STANDALONE_MARKERS: list[tuple[Pattern[str], str]] = [
    (re.compile(r"\bvibe[- ]coded\b", re.IGNORECASE), "vibe-coded"),
    (re.compile(r"\bai[- ]generated\b", re.IGNORECASE), "ai-generated"),
    (re.compile(r"\bai[- ]assisted\b", re.IGNORECASE), "ai-assisted"),
    (re.compile(r"\bvibe[- ]cod(?:ado|ed)\b", re.IGNORECASE), "vibe-coded"),
    (re.compile(r"\bgerado (?:por|com) ia\b", re.IGNORECASE), "ai-generated"),
    (re.compile(r"\bassistido por ia\b|\bcom (?:a )?assist[eê]ncia de ia\b", re.IGNORECASE), "ai-assisted"),
]

# Normalize captured tool names to stable slugs.
_TOOL_SLUGS: dict[str, str] = {
    "ai": "ai-generated",
    "ia": "ai-generated",
    "gpt": "chatgpt",
    "llm": "ai-generated",
    "bolt.new": "bolt",
}


class AiDeclarationDetector:
    """Detects that the addon author *declared*, in the AnkiWeb page description, that the addon was
    built with AI coding tools.

    Recognizes both English and Portuguese phrasings. Returns the sorted, de-duplicated tool slugs
    found. An empty list means no such declaration was detected -- never that the addon was *not*
    AI-assisted. Only self-referential build claims count; descriptions that merely mention AI as a
    feature are deliberately ignored.
    """

    @staticmethod
    def detect(description: Optional[str]) -> list[str]:
        if not description:
            return []
        markers: set[str] = set()
        for pattern in _BUILD_DECLARATIONS:
            for tool in pattern.findall(description):
                markers.add(AiDeclarationDetector.__slug(tool))
        for pattern in _MADE_WITHS:
            for tool in pattern.findall(description):
                markers.add(AiDeclarationDetector.__slug(tool))
        for pattern, slug in _STANDALONE_MARKERS:
            if pattern.search(description):
                markers.add(slug)
        return sorted(markers)

    @staticmethod
    def __slug(tool: str) -> str:
        lowered: str = tool.lower()
        return _TOOL_SLUGS.get(lowered, lowered)
