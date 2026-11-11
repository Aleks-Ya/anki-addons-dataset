import copy
import logging
import re
from collections import Counter
from logging import Logger
from typing import Callable, Optional

from anki_addons_dataset.collector.github.handler.manifest_parser import ManifestParser
from anki_addons_dataset.common.data_types import AddonId, AddonInfo, AddonInfos, AddonManifest, AddonPackage, \
    GithubInfo, GithubManifestFile

log: Logger = logging.getLogger(__name__)


class GithubManifestSelector:
    __common_file_names: frozenset[str] = frozenset(
        {"__init__.py", "manifest.json", "config.json", "config.md", "meta.json"})
    __common_file_prefixes: tuple[str, ...] = ("readme", "license")

    @staticmethod
    def select(addon_infos: AddonInfos) -> AddonInfos:
        rule_counts: Counter[str] = Counter()
        selected: list[AddonInfo] = []
        for addon_info in addon_infos:
            github: Optional[GithubInfo] = addon_info.github
            if github is None or len(github.manifest_files) < 2:
                selected.append(addon_info)
                continue
            rule, manifest_file = GithubManifestSelector.__choose(addon_info, github.manifest_files)
            rule_counts[rule] += 1
            selected.append(copy.replace(addon_info, github=copy.replace(
                github, manifest=manifest_file.manifest if manifest_file else None,
                manifest_path=manifest_file.path if manifest_file else None)))
        if rule_counts:
            log.info(f"Manifests chosen in repos with several manifest.json files: {dict(sorted(rule_counts.items()))}")
        return AddonInfos(selected)

    @staticmethod
    def __choose(addon_info: AddonInfo,
                 manifest_files: list[GithubManifestFile]) -> tuple[str, Optional[GithubManifestFile]]:
        package: Optional[AddonPackage] = max(addon_info.package.branches, key=lambda branch: branch.updated) \
            if addon_info.package and addon_info.package.branches else None
        rules: list[tuple[str, Callable[[], Optional[GithubManifestFile]]]] = [
            ("addon_id", lambda: GithubManifestSelector.__by_addon_id(addon_info.header.id, manifest_files)),
            ("package_manifest", lambda: GithubManifestSelector.__by_package_manifest(package, manifest_files)),
            ("file_names", lambda: GithubManifestSelector.__by_file_names(package, manifest_files))]
        for rule, choose in rules:
            manifest_file: Optional[GithubManifestFile] = choose()
            if manifest_file is not None:
                return rule, manifest_file
        return "undecided", None

    @staticmethod
    def __by_addon_id(addon_id: AddonId, manifest_files: list[GithubManifestFile]) -> Optional[GithubManifestFile]:
        id_pattern: re.Pattern[str] = re.compile(rf"(?<!\d){addon_id}(?!\d)")
        return GithubManifestSelector.__single([
            manifest_file for manifest_file in manifest_files
            if manifest_file.manifest and manifest_file.manifest.homepage
            and id_pattern.search(manifest_file.manifest.homepage)])

    @staticmethod
    def __by_package_manifest(package: Optional[AddonPackage],
                              manifest_files: list[GithubManifestFile]) -> Optional[GithubManifestFile]:
        package_manifest: Optional[AddonManifest] = ManifestParser.parse(package.manifest_json) if package else None
        if package_manifest is None:
            return None
        for value in [package_manifest.package, package_manifest.name]:
            if value is None:
                continue
            matches: list[GithubManifestFile] = [
                manifest_file for manifest_file in manifest_files if manifest_file.manifest
                and value in (manifest_file.manifest.package, manifest_file.manifest.name)]
            if len(matches) == 1:
                return matches[0]
        return None

    @staticmethod
    def __by_file_names(package: Optional[AddonPackage],
                        manifest_files: list[GithubManifestFile]) -> Optional[GithubManifestFile]:
        if package is None:
            return None
        package_files: set[str] = {file for file in package.files if GithubManifestSelector.__is_distinctive(file)}
        scored: list[tuple[int, GithubManifestFile]] = sorted(
            ((len(package_files.intersection(manifest_file.files)), manifest_file) for manifest_file in manifest_files),
            key=lambda item: item[0], reverse=True)
        best_score: int = scored[0][0]
        if best_score == 0 or scored[1][0] == best_score:
            return None
        return scored[0][1]

    @staticmethod
    def __is_distinctive(file: str) -> bool:
        name: str = file.rsplit("/", 1)[-1]
        return "__pycache__/" not in file and name not in GithubManifestSelector.__common_file_names \
            and not name.lower().startswith(GithubManifestSelector.__common_file_prefixes)

    @staticmethod
    def __single(manifest_files: list[GithubManifestFile]) -> Optional[GithubManifestFile]:
        return manifest_files[0] if len(manifest_files) == 1 else None
