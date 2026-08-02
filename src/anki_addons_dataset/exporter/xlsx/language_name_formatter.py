from typing import Optional

from lingua import IsoCode639_1, Language

from anki_addons_dataset.common.data_types import LanguageCode


class LanguageNameFormatter:
    """Renders a stored ISO-639-1 description-language code (e.g. "en") as a full English language
    name (e.g. "English") for the human-readable XLSX export. JSON/Parquet keep the raw code.
    """

    @staticmethod
    def name_of(code: Optional[LanguageCode]) -> Optional[str]:
        if not code:
            return None
        try:
            iso_code: IsoCode639_1 = getattr(IsoCode639_1, code.upper())
        except AttributeError:
            return None
        return Language.from_iso_code_639_1(iso_code).name.title()
