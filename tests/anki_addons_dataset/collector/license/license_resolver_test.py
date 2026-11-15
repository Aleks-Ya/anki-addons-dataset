from dataclasses import replace
from datetime import date
from typing import Optional

import pytest

from anki_addons_dataset.collector.license.license_resolver import LicenseResolver
from anki_addons_dataset.common.data_types import AddonDescription, AddonInfo, AddonInfos, AddonLicense, \
    AddonPackage, AddonPackages, AnkiPointVersion, GithubReadme, LicenseSource, PackageLicenseSource, SpdxLicense

__MIT_README: GithubReadme = GithubReadme("# Addon\n\nDoes things.\n\n## License\n\nMIT License\n")
__GPL_DESCRIPTION: AddonDescription = AddonDescription("Shows the note size. Licensed under the GNU GPL v3.")
__PLAIN_DESCRIPTION: AddonDescription = AddonDescription("Shows the note size.")


def __package(min_point_version: int, spdx_id: Optional[str] = None,
              source: Optional[PackageLicenseSource] = None) -> AddonPackage:
    return AddonPackage(f"{min_point_version}-2026-01-15-0123456789ab.ankiaddon", AnkiPointVersion(min_point_version),
                        date(2026, 1, 15), 10, None, None, 1, 6, 1, 1, ["__init__.py"], {}, None,
                        SpdxLicense(spdx_id) if spdx_id else None, source)


def __addon(addon_info: AddonInfo, package: Optional[AddonPackage] = None, github_license: Optional[str] = None,
            readme: Optional[GithubReadme] = None,
            description: AddonDescription = __PLAIN_DESCRIPTION) -> AddonInfo:
    github_spdx_id: Optional[SpdxLicense] = SpdxLicense(github_license) if github_license else None
    return replace(addon_info, package=AddonPackages([package]) if package else None,
                   github=replace(addon_info.github, license=github_spdx_id, readme=readme),
                   page=replace(addon_info.page, description=description))


def __resolve(addon_info: AddonInfo) -> Optional[AddonLicense]:
    return LicenseResolver.resolve(AddonInfos([addon_info]))[0].license


@pytest.mark.parametrize("package, github_license, readme, description, expected", [
    (__package(1, "MIT", PackageLicenseSource.FILE), "GPL-3.0", __MIT_README, __GPL_DESCRIPTION,
     AddonLicense(SpdxLicense("MIT"), LicenseSource.PACKAGE_FILE)),
    (__package(1, "AGPL-3.0", PackageLicenseSource.HEADER), "GPL-3.0", __MIT_README, __GPL_DESCRIPTION,
     AddonLicense(SpdxLicense("GPL-3.0"), LicenseSource.GITHUB)),
    (__package(1, "AGPL-3.0", PackageLicenseSource.HEADER), None, __MIT_README, __GPL_DESCRIPTION,
     AddonLicense(SpdxLicense("AGPL-3.0"), LicenseSource.PACKAGE_HEADER)),
    (None, None, __MIT_README, __GPL_DESCRIPTION, AddonLicense(SpdxLicense("MIT"), LicenseSource.README)),
    (None, None, None, __GPL_DESCRIPTION, AddonLicense(SpdxLicense("GPL-3.0"), LicenseSource.DESCRIPTION)),
    (None, "NOASSERTION", None, __GPL_DESCRIPTION, AddonLicense(SpdxLicense("GPL-3.0"), LicenseSource.DESCRIPTION)),
    (__package(1), None, None, __PLAIN_DESCRIPTION, None),
])
def test_resolve_takes_the_strongest_source(addon_info: AddonInfo, package: Optional[AddonPackage],
                                            github_license: Optional[str], readme: Optional[GithubReadme],
                                            description: AddonDescription, expected: Optional[AddonLicense]):
    assert __resolve(__addon(addon_info, package, github_license, readme, description)) == expected


def test_resolve_takes_the_package_license_of_the_newest_branch(addon_info: AddonInfo):
    addon_info = replace(__addon(addon_info), package=AddonPackages([
        __package(231000, "AGPL-3.0", PackageLicenseSource.FILE), __package(45, "MIT", PackageLicenseSource.FILE)]))

    assert __resolve(addon_info) == AddonLicense(SpdxLicense("AGPL-3.0"), LicenseSource.PACKAGE_FILE)


def test_resolve_works_without_github(addon_info: AddonInfo):
    addon_info = replace(addon_info, github=None, page=replace(addon_info.page, description=__GPL_DESCRIPTION))

    assert __resolve(addon_info) == AddonLicense(SpdxLicense("GPL-3.0"), LicenseSource.DESCRIPTION)


def test_resolve_logs_the_sources(addon_info: AddonInfo, caplog: pytest.LogCaptureFixture):
    LicenseResolver.resolve(AddonInfos([__addon(addon_info, github_license="MIT"), __addon(addon_info)]))

    assert "Addon licenses by source: {'github': 1}, none: 1" in caplog.text
