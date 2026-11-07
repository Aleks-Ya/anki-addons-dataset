import json
from importlib.resources import files
from typing import Any

import pytest
from magika import Magika

from anki_addons_dataset.collector.package.package_language_names import PackageLanguageNames
from anki_addons_dataset.common.data_types import LanguageName


def test_linguist_name_covers_every_code_label_magika_can_give():
    content_types: dict[str, Any] = json.loads(
        files("magika").joinpath("config/content_types_kb.min.json").read_text(encoding="utf-8"))
    code_labels: list[str] = [str(label) for label in Magika().get_output_content_types()
                              if content_types[str(label)]["group"] == "code"]

    assert len(code_labels) >= 83
    for label in code_labels:
        assert PackageLanguageNames.linguist_name(label)


@pytest.mark.parametrize("label, name", [
    ("python", "Python"), ("cpp", "C++"), ("asm", "Assembly"), ("ignorefile", "Ignore List"), ("csproj", "XML"),
    ("jsonl", "JSON"), ("mht", "MHTML")])
def test_linguist_name(label: str, name: str):
    assert PackageLanguageNames.linguist_name(label) == LanguageName(name)


def test_linguist_name_of_an_unknown_label():
    with pytest.raises(ValueError, match="No language name for the Magika label 'brainfuck'"):
        PackageLanguageNames.linguist_name("brainfuck")
