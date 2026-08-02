from anki_addons_dataset.collector.ankiweb.ai_declaration_detector import AiDeclarationDetector


def test_empty_or_none_returns_empty():
    assert AiDeclarationDetector.detect(None) == []
    assert AiDeclarationDetector.detect("") == []


def test_plain_description_returns_empty():
    assert AiDeclarationDetector.detect("A handy addon that reviews cards faster.") == []


def test_build_declaration_with_tool():
    assert AiDeclarationDetector.detect("This addon was built with ChatGPT over a weekend.") == ["chatgpt"]
    assert AiDeclarationDetector.detect("Entirely coded using Claude.") == ["claude"]
    assert AiDeclarationDetector.detect("Written with the help of Copilot.") == ["copilot"]


def test_build_declaration_generic_ai_maps_to_slug():
    assert AiDeclarationDetector.detect("Made with AI.") == ["ai-generated"]
    assert AiDeclarationDetector.detect("Developed using an LLM.") == ["ai-generated"]


def test_made_with_branded_tools():
    assert AiDeclarationDetector.detect("Made with Cursor") == ["cursor"]
    assert AiDeclarationDetector.detect("made with bolt.new") == ["bolt"]
    assert AiDeclarationDetector.detect("Made with Lovable") == ["lovable"]


def test_standalone_markers():
    assert AiDeclarationDetector.detect("This project was vibe-coded.") == ["vibe-coded"]
    assert AiDeclarationDetector.detect("An AI-generated helper.") == ["ai-generated"]
    assert AiDeclarationDetector.detect("AI-assisted development throughout.") == ["ai-assisted"]


def test_feature_mention_is_not_a_declaration():
    # Describing an AI *feature* is not a build declaration and must not be flagged.
    assert AiDeclarationDetector.detect("Generate flashcards with ChatGPT directly from Anki.") == []
    assert AiDeclarationDetector.detect("AI-powered card suggestions for your deck.") == []
    assert AiDeclarationDetector.detect("Ask Claude questions about your notes.") == []


def test_results_are_sorted_and_deduplicated():
    description: str = "Vibe-coded and made with Cursor, then refined with Cursor again."
    assert AiDeclarationDetector.detect(description) == ["cursor", "vibe-coded"]


def test_build_declaration_with_tool_pt():
    assert AiDeclarationDetector.detect("Este addon foi feito com ChatGPT.") == ["chatgpt"]
    assert AiDeclarationDetector.detect("Desenvolvido usando Claude.") == ["claude"]
    assert AiDeclarationDetector.detect("Escrito com a ajuda do Copilot.") == ["copilot"]


def test_build_declaration_generic_ai_maps_to_slug_pt():
    assert AiDeclarationDetector.detect("Feito com IA.") == ["ai-generated"]
    assert AiDeclarationDetector.detect("Desenvolvido usando um LLM.") == ["ai-generated"]


def test_made_with_branded_tools_pt():
    assert AiDeclarationDetector.detect("Feito com Cursor") == ["cursor"]
    assert AiDeclarationDetector.detect("feito com bolt.new") == ["bolt"]
    assert AiDeclarationDetector.detect("Feito com Lovable") == ["lovable"]


def test_standalone_markers_pt():
    assert AiDeclarationDetector.detect("Este projeto foi vibe-codado.") == ["vibe-coded"]
    assert AiDeclarationDetector.detect("Gerado por IA.") == ["ai-generated"]
    assert AiDeclarationDetector.detect("Assistido por IA durante todo o desenvolvimento.") == ["ai-assisted"]
    assert AiDeclarationDetector.detect("O código foi revisado com assistência de IA.") == ["ai-assisted"]


def test_feature_mention_is_not_a_declaration_pt():
    assert AiDeclarationDetector.detect("Gere flashcards com ChatGPT diretamente do Anki.") == []
    assert AiDeclarationDetector.detect("Sugestões de cartões com tecnologia de IA para o seu baralho.") == []
    assert AiDeclarationDetector.detect("Pergunte ao Claude sobre suas notas.") == []


def test_results_are_sorted_and_deduplicated_mixed_languages():
    description: str = "Vibe-coded and also feito com Cursor, then refined usando Claude."
    assert AiDeclarationDetector.detect(description) == ["claude", "cursor", "vibe-coded"]
