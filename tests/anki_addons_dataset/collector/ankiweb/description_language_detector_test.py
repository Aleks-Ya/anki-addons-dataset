from anki_addons_dataset.collector.ankiweb.description_language_detector import DescriptionLanguageDetector


def test_empty_or_none_returns_unknown():
    assert DescriptionLanguageDetector.detect(None) == (None, None)
    assert DescriptionLanguageDetector.detect("") == (None, None)
    assert DescriptionLanguageDetector.detect("   ") == (None, None)


def test_too_short_returns_unknown():
    assert DescriptionLanguageDetector.detect("Hi") == (None, None)


def test_no_letters_returns_unknown():
    assert DescriptionLanguageDetector.detect("1234567890 !!! ??? ...") == (None, None)


def test_detects_english():
    code, confidence = DescriptionLanguageDetector.detect(
        "This addon adds spaced repetition review shortcuts to your Anki collection.")
    assert code == "en"
    assert confidence is not None
    assert 0.0 < confidence <= 1.0


def test_detects_spanish():
    code, confidence = DescriptionLanguageDetector.detect(
        "Este complemento añade atajos para repasar tarjetas en tu colección de Anki.")
    assert code == "es"
    assert confidence is not None
    assert 0.0 < confidence <= 1.0


def test_is_deterministic():
    text: str = "This addon adds spaced repetition review shortcuts to your Anki collection."
    first = DescriptionLanguageDetector.detect(text)
    second = DescriptionLanguageDetector.detect(text)
    assert first == second
