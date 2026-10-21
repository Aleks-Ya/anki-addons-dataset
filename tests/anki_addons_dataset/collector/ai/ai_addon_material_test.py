from anki_addons_dataset.collector.ai.ai_addon_material import AiAddonMaterial
from anki_addons_dataset.common.data_types import AddonTitle, AddonDescription, GithubReadme


def test_material_holds_the_addon_texts() -> None:
    material: str = AiAddonMaterial(8000).format(
        AddonTitle("Note Size"), AddonDescription("Displays the size of notes."), GithubReadme("A README."))

    assert material == ("<addon_title>\nNote Size\n</addon_title>\n\n"
                        "<addon_description>\nDisplays the size of notes.\n</addon_description>\n\n"
                        "<addon_github_readme>\nA README.\n</addon_github_readme>")


def test_missing_description_and_readme_are_stated() -> None:
    material: str = AiAddonMaterial(8000).format(AddonTitle("Note Size"), AddonDescription(""), None)

    assert "No description provided." in material
    assert "No README provided." in material


def test_multi_line_texts_are_not_indented() -> None:
    material: str = AiAddonMaterial(8000).format(
        AddonTitle("Note Size"), AddonDescription("Line one\nLine two"), GithubReadme("# Title\n\nBody"))

    assert not any(line.startswith(" ") for line in material.splitlines())


def test_braces_in_texts_are_kept() -> None:
    material: str = AiAddonMaterial(8000).format(
        AddonTitle("{title}"), AddonDescription("{description}"), GithubReadme("{readme}"))

    assert "{title}" in material
    assert "{description}" in material
    assert "{readme}" in material


def test_long_readme_is_truncated() -> None:
    readme: GithubReadme = AiAddonMaterial(10).truncate(GithubReadme("0123456789-this-part-is-dropped"))

    assert readme == "0123456789\n\n(README truncated.)"


def test_short_readme_is_kept_whole() -> None:
    assert AiAddonMaterial(10).truncate(GithubReadme("0123456789")) == "0123456789"


def test_missing_readme_stays_missing() -> None:
    assert AiAddonMaterial(10).truncate(None) is None
