import datetime
from typing import Optional

from anki_addons_dataset.collector.ankiforum.ankiforum_topic_selector import AnkiForumTopicSelector
from anki_addons_dataset.collector.ankiweb.addon_page_parser import AddonPageParser
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonHeader, AddonId, AddonRating, AddonTitle, AnkiForumTopicSource, \
    AnkiVersion, HtmlStr, UpdateDate, URL


def __decided_topic(overrider: Overrider, addon_id: int, html: str
                    ) -> Optional[tuple[URL, AnkiForumTopicSource]]:
    header: AddonHeader = AddonHeader(
        id=AddonId(addon_id),
        title=AddonTitle("Some addon"),
        addon_page_url=URL(f"https://ankiweb.net/shared/info/{addon_id}"),
        rating=AddonRating(0),
        update_date=UpdateDate(datetime.date(2025, 4, 19)),
        anki_version=AnkiVersion("25.09.2~"))
    page_html: HtmlStr = HtmlStr(f'<html><body><main>{html}</main></body></html>')
    return AnkiForumTopicSelector(overrider).decided_topic(AddonPageParser().parse_addon_page(header, page_html))


def __description(*urls: str) -> str:
    anchors: str = "".join(f'<a href="{url}">Link</a>' for url in urls)
    return f'<div class="shared-item-description">{anchors}</div>'


def test_contact_author_forum_link_wins_over_description_vote(overrider: Overrider):
    """The Contact Author button's forum URL beats a differently-voted forum URL in the description."""
    decided: Optional[tuple[URL, AnkiForumTopicSource]] = __decided_topic(
        overrider, 3,
        '<a class="btn btn-outline-primary" '
        'href="https://forums.ankiweb.net/t/review-heatmap-official-support-thread/928/1">Contact Author</a>'
        + __description("https://forums.ankiweb.net/t/some-other-thread/1",
                        "https://forums.ankiweb.net/t/some-other-thread/1",
                        "https://forums.ankiweb.net/t/some-other-thread/1"))
    assert decided == (URL("https://forums.ankiweb.net/t/review-heatmap-official-support-thread/928/1"),
                       AnkiForumTopicSource.CONTACT_AUTHOR)


def test_manual_override_beats_contact_author_forum_link(overrider: Overrider):
    """An overrides.yaml forum URL (addon 111623432) still wins over the Contact Author button."""
    decided: Optional[tuple[URL, AnkiForumTopicSource]] = __decided_topic(
        overrider, 111623432,
        '<a class="btn btn-outline-primary" href="https://forums.ankiweb.net/t/wrong-thread/999">Contact Author</a>')
    assert decided == (URL("https://forums.ankiweb.net/t/hypertts-spirtual-successor-to-awesometts/17143"),
                       AnkiForumTopicSource.OVERRIDE)


def test_no_contact_author_button_falls_back_to_description_vote(overrider: Overrider):
    """Without a Contact Author button the forum URL still comes from the description majority vote."""
    decided: Optional[tuple[URL, AnkiForumTopicSource]] = __decided_topic(
        overrider, 5, __description("https://forums.ankiweb.net/t/the-only-thread/42"))
    assert decided == (URL("https://forums.ankiweb.net/t/the-only-thread/42"), AnkiForumTopicSource.MOST_LINKED)


def test_description_vote_counts_repeated_links(overrider: Overrider):
    decided: Optional[tuple[URL, AnkiForumTopicSource]] = __decided_topic(
        overrider, 6, __description("https://forums.ankiweb.net/t/a-thread/1",
                                    "https://forums.ankiweb.net/t/b-thread/2",
                                    "https://forums.ankiweb.net/t/b-thread/2"))
    assert decided == (URL("https://forums.ankiweb.net/t/b-thread/2"), AnkiForumTopicSource.MOST_LINKED)


def test_description_vote_tie_goes_to_the_first_url_in_sort_order(overrider: Overrider):
    decided: Optional[tuple[URL, AnkiForumTopicSource]] = __decided_topic(
        overrider, 7, __description("https://forums.ankiweb.net/t/b-thread/2",
                                    "https://forums.ankiweb.net/t/a-thread/1"))
    assert decided == (URL("https://forums.ankiweb.net/t/a-thread/1"), AnkiForumTopicSource.MOST_LINKED)


def test_no_forum_link_decides_nothing(overrider: Overrider):
    assert __decided_topic(overrider, 8, __description("https://github.com/user/repo")) is None
