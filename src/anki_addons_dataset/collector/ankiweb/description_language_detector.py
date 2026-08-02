import re
from typing import Optional, Pattern

from lingua import LanguageDetector, LanguageDetectorBuilder

from anki_addons_dataset.common.data_types import LanguageCode

# Detect the natural (human) language of the AnkiWeb addon-page description -- e.g. English, Spanish.
# Distinct from GithubInfo.languages, which are *programming* languages.

# The lingua detector loads per-language models and is expensive to build, so it is created once and
# shared across all addons. lingua lazy-loads each language model on first use (memory stays bounded).
_detector: Optional[LanguageDetector] = None

# The detected language is deterministic, but the raw confidence float jitters in its last bits between
# runs (floating-point summation order inside lingua). PARSE re-parses the whole snapshot history every
# run, so we round the confidence to keep dumps/reports byte-stable run-to-run. Four decimals is ample
# precision for a confidence score.
_CONFIDENCE_DECIMALS: int = 4

# Descriptions shorter than this (after stripping) are too little signal to classify reliably; the
# author's intent is unknowable from a word or two, so we report "unknown" rather than guess.
_MIN_LENGTH: int = 10

# A description must contain at least one letter -- pure punctuation/URLs/numbers carry no language.
_HAS_LETTER: Pattern[str] = re.compile(r"[^\W\d_]", re.UNICODE)


class DescriptionLanguageDetector:
    """Detects the dominant natural language of an addon description.

    Returns a `(iso_639_1_code, confidence)` tuple -- e.g. `("en", 0.99)`. Both are `None` when the
    description is empty, too short, or carries no letters: an honest "unknown" rather than a guess.
    """

    @staticmethod
    def detect(description: Optional[str]) -> tuple[Optional[LanguageCode], Optional[float]]:
        if not description:
            return None, None
        text: str = description.strip()
        if len(text) < _MIN_LENGTH or _HAS_LETTER.search(text) is None:
            return None, None
        confidence_values = DescriptionLanguageDetector.__get_detector().compute_language_confidence_values(text)
        if not confidence_values:
            return None, None
        top = confidence_values[0]
        iso_code = top.language.iso_code_639_1
        if iso_code is None:
            return None, None
        return LanguageCode(iso_code.name.lower()), round(float(top.value), _CONFIDENCE_DECIMALS)

    @staticmethod
    def __get_detector() -> LanguageDetector:
        global _detector
        if _detector is None:
            _detector = LanguageDetectorBuilder.from_all_languages().build()
        return _detector
