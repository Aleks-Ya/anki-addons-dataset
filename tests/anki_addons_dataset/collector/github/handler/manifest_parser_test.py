from anki_addons_dataset.collector.github.handler.manifest_parser import ManifestParser
from anki_addons_dataset.common.data_types import AddonManifest


def test_parse_full_manifest():
    content: str = """{"package":"note_size","name":"Note Size","conflicts":["123","456"],
        "min_point_version":45,"max_point_version":50,"homepage":"https://example.com","mod":1678900000}"""
    assert ManifestParser.parse(content) == AddonManifest(
        package="note_size", name="Note Size", conflicts=["123", "456"], min_point_version=45,
        max_point_version=50, homepage="https://example.com", mod=1678900000)


def test_parse_minimal_manifest():
    assert ManifestParser.parse("""{"package":"x"}""") == AddonManifest(package="x")


def test_parse_none_and_empty():
    assert ManifestParser.parse(None) is None
    assert ManifestParser.parse("") is None


def test_parse_malformed_json_returns_none():
    assert ManifestParser.parse("{not json") is None


def test_parse_non_object_returns_none():
    assert ManifestParser.parse("[1, 2, 3]") is None


def test_parse_ignores_non_int_versions():
    manifest: AddonManifest = ManifestParser.parse("""{"min_point_version":"45","mod":"x"}""")
    assert manifest.min_point_version is None
    assert manifest.mod is None
