from typing import Optional

from anki_addons_dataset.collector.aggregator import Aggregator
from anki_addons_dataset.common.data_types import Aggregation, AddonInfos, AddonInfo, AnkiForumInfo


def test_aggregate(aggregator: Aggregator, addon_infos: AddonInfos):
    aggregation: Aggregation = aggregator.aggregate(addon_infos)
    assert aggregation == Aggregation(
        addon_number=1,
        addon_with_github_number=1,
        addon_with_anki_forum_page_number=1,
        addon_with_unit_tests_number=1
    )


def test_aggregate_empty(aggregator: Aggregator):
    aggregation: Aggregation = aggregator.aggregate(AddonInfos([]))
    assert aggregation == Aggregation(
        addon_number=0,
        addon_with_github_number=0,
        addon_with_anki_forum_page_number=0,
        addon_with_unit_tests_number=0
    )


def test_aggregate_empty_forum(aggregator: Aggregator, addon_info: AddonInfo):
    forum: Optional[AnkiForumInfo] = None
    addon_info.forum = forum
    addon_infos: AddonInfos = AddonInfos([addon_info])
    aggregation: Aggregation = aggregator.aggregate(addon_infos)
    assert aggregation == Aggregation(
        addon_number=1,
        addon_with_github_number=1,
        addon_with_anki_forum_page_number=0,
        addon_with_unit_tests_number=1
    )
