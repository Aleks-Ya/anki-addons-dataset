from anki_addons_dataset.aggregator.aggregator import Aggregator
from anki_addons_dataset.common.data_types import Aggregation, AddonInfos


def test_aggregate_empty():
    aggregator: Aggregator = Aggregator()
    aggregation: Aggregation = aggregator.aggregate(AddonInfos([]))
    assert aggregation == Aggregation(
        addon_number=0,
        addon_with_github_number=0,
        addon_with_anki_forum_page_number=0,
        addon_with_unit_tests_number=0
    )


def test_aggregate(addon_infos: AddonInfos):
    aggregator: Aggregator = Aggregator()
    aggregation: Aggregation = aggregator.aggregate(addon_infos)
    assert aggregation == Aggregation(
        addon_number=1,
        addon_with_github_number=1,
        addon_with_anki_forum_page_number=1,
        addon_with_unit_tests_number=1
    )
