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
    manifest: AddonManifest = ManifestParser.parse(
        """{"package":"x","name":"X","min_point_version":"45","mod":"x"}""")
    assert manifest.min_point_version is None
    assert manifest.mod is None


def test_parse_object_package_is_ignored():
    content: str = """{"package":{"name":"Pronounce Symbol Generator","version":"1.0.0",
        "description":"Easily add phonetic symbols to your notes!","author":"omuomuMG"}}"""
    assert ManifestParser.parse(content) is None


def test_parse_missing_package_is_ignored():
    assert ManifestParser.parse("""{"name":"X"}""") is None


def test_parse_non_string_name_or_homepage_ignored():
    assert ManifestParser.parse("""{"package":"x","name":{"a":1}}""") is None
    assert ManifestParser.parse("""{"package":"x","homepage":{"a":1}}""") is None
