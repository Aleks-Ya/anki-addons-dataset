from dataclasses import replace
from datetime import date
from typing import Optional

from anki_addons_dataset.collector.github.github_manifest_selector import GithubManifestSelector
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AddonManifest, AddonPackage, \
    AddonPackages, AnkiPointVersion, GithubInfo, GithubManifestFile, URL


def __package(files: list[str], manifest_json: Optional[str] = None,
              updated: date = date(2026, 1, 1)) -> AddonPackage:
    return AddonPackage("45-2026-01-01-aaaaaaaaaaaa.ankiaddon", AnkiPointVersion(45), updated, 100, manifest_json,
                        None, len(files), 100, 0, 0, files, {})


def __addon(addon_info: AddonInfo, manifest_files: list[GithubManifestFile],
            packages: Optional[list[AddonPackage]] = None) -> AddonInfo:
    assert addon_info.github is not None
    first: GithubManifestFile = manifest_files[0]
    return replace(addon_info, header=replace(addon_info.header, id=AddonId(1234567)),
                   github=replace(addon_info.github, manifest=first.manifest, manifest_path=first.path,
                                  manifest_files=manifest_files if len(manifest_files) > 1 else []),
                   package=AddonPackages(packages) if packages else None)


def __select(addon_info: AddonInfo) -> tuple[Optional[str], Optional[AddonManifest]]:
    github: Optional[GithubInfo] = GithubManifestSelector.select(AddonInfos([addon_info]))[0].github
    assert github is not None
    return github.manifest_path, github.manifest


__root: GithubManifestFile = GithubManifestFile("manifest.json", AddonManifest(package="root", name="Root"),
                                                ["manifest.json", "root.py"])
__a: GithubManifestFile = GithubManifestFile("a/manifest.json", AddonManifest(package="a", name="Addon A"),
                                             ["manifest.json", "__init__.py", "a.py", "util.py"])
__b: GithubManifestFile = GithubManifestFile(
    "b/manifest.json", AddonManifest(package="b", name="Addon B", homepage=URL("https://ankiweb.net/shared/info/1234567")),
    ["manifest.json", "__init__.py", "b.py", "util.py"])


def test_the_addon_id_in_the_homepage_wins(addon_info: AddonInfo):
    addon: AddonInfo = __addon(addon_info, [__root, __a, __b], [__package(["a.py"], '{"package": "a"}')])
    assert __select(addon) == ("b/manifest.json", __b.manifest)


def test_the_package_manifest_matches_by_package_then_name(addon_info: AddonInfo):
    by_package: AddonInfo = __addon(addon_info, [__root, __a], [__package([], '{"package": "a"}')])
    by_name: AddonInfo = __addon(addon_info, [__root, __a], [__package([], '{"package": "x", "name": "Addon A"}')])
    assert __select(by_package) == ("a/manifest.json", __a.manifest)
    assert __select(by_name) == ("a/manifest.json", __a.manifest)


def test_the_newest_branch_is_used(addon_info: AddonInfo):
    addon: AddonInfo = __addon(addon_info, [__root, __a], [
        __package([], '{"package": "root"}', date(2026, 2, 1)), __package([], '{"package": "a"}', date(2025, 1, 1))])
    assert __select(addon) == ("manifest.json", __root.manifest)


def test_the_file_names_decide_ignoring_common_files(addon_info: AddonInfo):
    addon: AddonInfo = __addon(addon_info, [__root, __a, replace(__b, manifest=AddonManifest(package="b"))],
                               [__package(["__init__.py", "manifest.json", "README.md", "a.py", "util.py"])])
    assert __select(addon) == ("a/manifest.json", __a.manifest)


def test_tied_file_names_leave_no_manifest(addon_info: AddonInfo):
    addon: AddonInfo = __addon(addon_info, [__root, __a, replace(__b, manifest=AddonManifest(package="b"))],
                               [__package(["__init__.py", "util.py"])])
    assert __select(addon) == (None, None)


def test_a_chosen_file_that_was_not_downloaded_keeps_its_path(addon_info: AddonInfo):
    addon: AddonInfo = __addon(addon_info, [__root, replace(__a, manifest=None)], [__package(["a.py"])])
    assert __select(addon) == ("a/manifest.json", None)


def test_an_addon_without_a_package_gets_no_manifest(addon_info: AddonInfo):
    addon: AddonInfo = __addon(addon_info, [__root, __a])
    assert __select(addon) == (None, None)


def test_a_repo_with_one_manifest_is_left_as_it_is(addon_info: AddonInfo):
    addon: AddonInfo = __addon(addon_info, [__a])
    assert __select(addon) == ("a/manifest.json", __a.manifest)
