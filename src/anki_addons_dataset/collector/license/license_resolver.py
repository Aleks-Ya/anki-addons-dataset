import copy
import logging
from collections import Counter
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.license.license_classifier import LicenseClassifier
from anki_addons_dataset.common.data_types import AddonInfo, AddonInfos, AddonLicense, AddonPackage, LicenseSource, \
    PackageLicenseSource, SpdxLicense

log: Logger = logging.getLogger(__name__)


class LicenseResolver:
    __unidentified_github_license: str = "NOASSERTION"

    @staticmethod
    def resolve(addon_infos: AddonInfos) -> AddonInfos:
        resolved: list[AddonInfo] = [copy.replace(addon_info, license=LicenseResolver.__license(addon_info))
                                     for addon_info in addon_infos]
        source_counts: Counter[str] = Counter(str(addon_info.license.source) for addon_info in resolved
                                              if addon_info.license is not None)
        log.info(f"Addon licenses by source: {dict(sorted(source_counts.items()))}, "
                 f"none: {len(resolved) - source_counts.total()}")
        return AddonInfos(resolved)

    @staticmethod
    def __license(addon_info: AddonInfo) -> Optional[AddonLicense]:
        newest: Optional[AddonPackage] = max(addon_info.package.branches, key=lambda branch: branch.min_point_version) \
            if addon_info.package is not None else None
        github_license: Optional[SpdxLicense] = addon_info.github.license if addon_info.github is not None else None
        readme: Optional[str] = addon_info.github.readme if addon_info.github is not None else None
        candidates: list[tuple[LicenseSource, Optional[SpdxLicense]]] = [
            (LicenseSource.PACKAGE_FILE, LicenseResolver.__package_license(newest, PackageLicenseSource.FILE)),
            (LicenseSource.GITHUB, github_license
             if github_license != LicenseResolver.__unidentified_github_license else None),
            (LicenseSource.PACKAGE_HEADER, LicenseResolver.__package_license(newest, PackageLicenseSource.HEADER)),
            (LicenseSource.README, LicenseClassifier.from_readme(readme) if readme else None),
            (LicenseSource.DESCRIPTION, LicenseClassifier.from_text(addon_info.page.description)),
        ]
        return next((AddonLicense(spdx_id, source) for source, spdx_id in candidates if spdx_id is not None), None)

    @staticmethod
    def __package_license(package: Optional[AddonPackage], source: PackageLicenseSource) -> Optional[SpdxLicense]:
        return package.license if package is not None and package.license_source == source else None
