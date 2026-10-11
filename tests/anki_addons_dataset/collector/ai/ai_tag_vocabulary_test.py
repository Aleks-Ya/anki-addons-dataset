from anki_addons_dataset.collector.ai.ai_tag_vocabulary import AiTagVocabulary
from anki_addons_dataset.common.data_types import AiTagDefinition, AiTag, AiTagGroup


def test_definitions_hold_every_tag() -> None:
    definitions: list[AiTagDefinition] = AiTagVocabulary.definitions()

    assert len(definitions) == 39
    assert len({definition.name for definition in definitions}) == 39


def test_definitions_list_function_tags_before_status_tags() -> None:
    groups: list[str] = [definition.group for definition in AiTagVocabulary.definitions()]

    assert groups == ["function"] * 32 + ["status"] * 7


def test_definition_carries_the_description() -> None:
    definitions: list[AiTagDefinition] = AiTagVocabulary.definitions()

    assert definitions[0] == AiTagDefinition(
        AiTag("card-creation"), AiTagGroup("function"),
        "Building notes from text, words, clipboard; field auto-fill")
    assert definitions[-1] == AiTagDefinition(AiTag("beta"), AiTagGroup("status"), "Self-declared alpha, beta or WIP")
