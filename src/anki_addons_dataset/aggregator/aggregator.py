from typing import cast

from anki_addons_dataset.common.data_types import Aggregation, AddonInfos, AddonInfo


class Aggregator:

    @staticmethod
    def aggregate(addon_infos: AddonInfos) -> Aggregation:
        addon_number: int = len(cast(list[AddonInfo], addon_infos))
        addon_with_github_number: int = len([addon for addon in addon_infos
                                             if addon.github.github_repo is not None])
        addon_with_anki_forum_page_number: int = len([addon for addon in addon_infos
                                                      if addon.page.anki_forum_url is not None])
        addon_with_unit_tests_number: int = len([addon for addon in addon_infos
                                                 if addon.github.tests_count and addon.github.tests_count > 0])
        return Aggregation(addon_number, addon_with_github_number, addon_with_anki_forum_page_number,
                           addon_with_unit_tests_number)
