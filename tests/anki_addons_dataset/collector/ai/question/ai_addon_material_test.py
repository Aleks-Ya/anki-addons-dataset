import copy

from anki_addons_dataset.collector.ai.provider.ai_provider import AiResponseText
from anki_addons_dataset.collector.ai.question.ai_addon_material import AiAddonMaterial
from anki_addons_dataset.common.data_types import AddonTitle, AddonDescription, AddonInfo, GithubReadme, PageLink, \
    PageLinkSection, URL


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


def test_answer_is_normalized() -> None:
    assert AiAddonMaterial.normalize_answer(AiResponseText(" `None.` \n")) == "none"


def test_link_texts_of_matching_links_are_deduplicated(addon_info: AddonInfo) -> None:
    links: list[PageLink] = [
        PageLink(URL("https://github.com/a/b"), PageLinkSection.DESCRIPTION, 1, ["source", "code"]),
        PageLink(URL("https://example.com"), PageLinkSection.DESCRIPTION, 1, ["site"]),
        PageLink(URL("https://github.com/a/b/issues"), PageLinkSection.DESCRIPTION, 1, ["code", "issues"]),
    ]
    info: AddonInfo = copy.replace(addon_info, page=copy.replace(addon_info.page, links=links))

    texts: list[str] = AiAddonMaterial.link_texts(info, lambda url: url.startswith("https://github.com/a/b"))

    assert texts == ["source", "code", "issues"]
