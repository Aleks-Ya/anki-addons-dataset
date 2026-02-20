from datetime import datetime

from anki_addons_dataset.aggregator.aggregator import Aggregator
from anki_addons_dataset.common.data_types import Aggregation, AddonInfo, AddonHeader, AddonPage, GithubInfo, \
    GitHubRepo, LanguageName, AddonId, URL, AddonInfos


def test_aggregate_empty():
    aggregator: Aggregator = Aggregator()
    aggregation: Aggregation = aggregator.aggregate(AddonInfos([]))
    assert aggregation == Aggregation(
        addon_number=0,
        addon_with_github_number=0,
        addon_with_anki_forum_page_number=0,
        addon_with_unit_tests_number=0
    )


def test_aggregate(note_size_addon_id: AddonId, github_repo: GitHubRepo):
    addon_infos: AddonInfos = AddonInfos([
        AddonInfo(
            header=AddonHeader(note_size_addon_id, "NoteSize", "https://ankiweb.net/shared/info/1188705668",
                               4, "2023-03-15", "1.0.0"),
            page=AddonPage(
                like_number=0,
                dislike_number=0,
                versions=[],
                other_links=[],
                anki_forum_url=URL("https://forums.ankiweb.net/t/note-size-addon-support/46001")
            ),
            github=GithubInfo(
                github_links=[],
                github_repo=github_repo,
                languages=[LanguageName("Python"), LanguageName("Rust")],
                stars=3,
                last_commit=datetime(2023, 3, 15, 12, 0, 0, 0),
                action_count=5,
                tests_count=7
            ),
            forum=None)
    ])
    aggregator: Aggregator = Aggregator()
    aggregation: Aggregation = aggregator.aggregate(addon_infos)
    assert aggregation == Aggregation(
        addon_number=1,
        addon_with_github_number=1,
        addon_with_anki_forum_page_number=1,
        addon_with_unit_tests_number=1
    )
