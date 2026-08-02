from anki_addons_dataset.common.data_types import LanguageCode
from anki_addons_dataset.exporter.xlsx.language_name_formatter import LanguageNameFormatter


def test_known_codes_render_full_names():
    assert LanguageNameFormatter.name_of(LanguageCode("en")) == "English"
    assert LanguageNameFormatter.name_of(LanguageCode("es")) == "Spanish"
    assert LanguageNameFormatter.name_of(LanguageCode("zh")) == "Chinese"


def test_none_or_empty_returns_none():
    assert LanguageNameFormatter.name_of(None) is None
    assert LanguageNameFormatter.name_of(LanguageCode("")) is None


def test_unknown_code_returns_none():
    assert LanguageNameFormatter.name_of(LanguageCode("xx")) is None
