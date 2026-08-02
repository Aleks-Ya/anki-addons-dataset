import datetime
from pathlib import Path

from anki_addons_dataset.collector.ankiweb.addon_page_parser import AddonPageParser
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonHeader, AddonInfo, AddonPage, GithubInfo, AddonId, GitHubLink, \
    URL, GitHubUser, GithubRepo, GithubUserName, GithubRepoName, AddonBranch, HtmlStr, AnkiForumInfo, AnkiVersion, \
    AddonRating, UpdateDate, AddonTitle, PlainStr


def test_parse_addon_page(overrider: Overrider):
    addon_html_file: Path = Path(__file__).parent / "1188705668.html"
    addon_html: HtmlStr = HtmlStr(addon_html_file.read_text())
    parser: AddonPageParser = AddonPageParser(overrider)
    addon_header: AddonHeader = AddonHeader(
        id=AddonId(1188705668),
        title=AddonTitle("Note Size - sort notes by size and see collection size"),
        addon_page_url=URL("https://ankiweb.net/shared/info/1188705668"),
        rating=AddonRating(12),
        update_date=UpdateDate("2025-04-19"),
        anki_version=AnkiVersion("25.09.2~"))
    addon_info: AddonInfo = parser.parse_addon_page(addon_header, addon_html)
    assert addon_info.page.description_language == "en"
    assert addon_info.page.description_language_confidence is not None
    assert 0.0 < addon_info.page.description_language_confidence <= 1.0
    # Null the (deterministic but verbose) language fields so the structural comparison below stays focused.
    addon_info.page.description_language = None
    addon_info.page.description_language_confidence = None
    github_user: GitHubUser = GitHubUser(GithubUserName("aleks-ya"))
    github_repo: GithubRepo = GithubRepo(GithubUserName("aleks-ya"), GithubRepoName("note-size-anki-addon"))
    assert addon_info == AddonInfo(
        addon_header,
        AddonPage(
            content=HtmlStr(addon_html),
            like_number=12,
            dislike_number=0,
            branches=[AddonBranch(min_anki_version=AnkiVersion('24.04.1'),
                                  max_anki_version=AnkiVersion('25.02.1+'),
                                  updated=datetime.date(2025, 4, 19))],
            other_links=[
                URL('https://ankiweb.net/logo.png'),
                URL('https://ankiweb.net/_app/immutable/nodes/0.DbG5vJiZ.mjs'),
                URL('https://ankiweb.net/_app/immutable/chunks/globals.D0QH3NT1.mjs'),
                URL('https://ankiweb.net/_app/immutable/chunks/stores.BJ8ZxSZM.mjs'),
                URL('https://ankiweb.net/_app/immutable/chunks/Alert.CUuPSeE_.mjs'),
                URL('https://ankiweb.net/_app/immutable/chunks/index.C5cLDmO0.mjs'),
                URL('https://ankiweb.net/_app/immutable/chunks/page.ByHWqWt2.mjs'),
                URL('https://ankiweb.net/_app/immutable/chunks/progress.C5qn9CQ9.mjs'),
                URL('https://ankiweb.net/_app/immutable/chunks/layout.CsEJWO6K.mjs'),
                URL('https://ankiweb.net/_app/immutable/assets/0.Cjzb4GXD.css'),
                URL('https://ankiweb.net/_app/immutable/nodes/1.ClqbUf4k.mjs'),
                URL('https://ankiweb.net/_app/immutable/nodes/25.DTiY_S_r.mjs'),
                URL('https://ankiweb.net/_app/immutable/chunks/frontend.DVIIEEoF.mjs'),
                URL('https://ankiweb.net/_app/immutable/chunks/each.BzHth1_T.mjs'),
                URL('https://ankiweb.net/_app/immutable/chunks/like.DEjprW7c.mjs'),
                URL('https://ankiweb.net/_app/immutable/chunks/SubmitButton.CmZ4Zv8R.mjs'),
                URL('https://ankiweb.net/_app/immutable/chunks/Title.D_1bBf-x.mjs'),
                URL('https://ankiweb.net/_app/immutable/chunks/utils.FdcdUtur.mjs'),
                URL('https://ankiweb.net/_app/immutable/assets/25.ClMJ9IEQ.css'),
                URL('https://raw.githubusercontent.com/Aleks-Ya/note-size-anki-addon/main/docs/images/collection-size.png'),
                URL('https://raw.githubusercontent.com/Aleks-Ya/note-size-anki-addon/main/docs/images/note-size-in-browser.png'),
                URL('https://raw.githubusercontent.com/Aleks-Ya/note-size-anki-addon/main/docs/images/sort-notes-by-size.png'),
                URL('https://raw.githubusercontent.com/Aleks-Ya/note-size-anki-addon/main/docs/images/notes-size.png'),
                URL('https://raw.githubusercontent.com/Aleks-Ya/note-size-anki-addon/main/docs/images/deck-size.png'),
                URL('https://raw.githubusercontent.com/Aleks-Ya/note-size-anki-addon/main/docs/images/add-note.png'),
                URL('https://raw.githubusercontent.com/Aleks-Ya/note-size-anki-addon/main/docs/images/open-config.png'),
                URL('https://forums.ankiweb.net/t/note-size-addon-support/46001'),
                URL('https://forums.ankiweb.net/t/note-size-addon-support/46001'),
                URL('https://forums.ankiweb.net/t/note-size-addon-support/46001'),
                URL('https://forums.ankiweb.net/t/note-size-addon-support/46001'),
                URL('https://sonarcloud.io/summary/new_code?id=Aleks-Ya_note-size-anki-addon'),
                URL('https://sonarcloud.io/api/project_badges/measure?project=Aleks-Ya_note-size-anki-addon&amp;metric=alert_status'),
                URL('https://sonarcloud.io/summary/new_code?id=Aleks-Ya_note-size-anki-addon'),
                URL('https://sonarcloud.io/api/project_badges/measure?project=Aleks-Ya_note-size-anki-addon&amp;metric=coverage'),
                URL('https://ankiweb.net/shared/info/1151815987'),
                URL('https://github.com/Aleks-Ya/note-size-anki-addon/blob/main/description/configuration.md#logging-level'),
                URL('https://apps.ankiweb.net')
            ],
            description=PlainStr('"Note Size" addon displays detailed information about size ("in bytes") of your '
                        'collection and individual notes including attachments. Screenshots Size of collection, media '
                        'files, unused media files, trash files, revision log Size of a note Sort notes by size Size '
                        'of found notes Size of a deck Size when adding a new note Open configuration dialog Contacts '
                        'If you have a question , please, reply at Support page at Anki Forum . If you met a bug , '
                        'create an issue at GitHub bug tracker or reply at Support page at Anki Forum . If you have a '
                        'feature request or another idea, reply at Support page at Anki Forum . For more details see '
                        'User Manual . Links Support page at Anki Forum GitHub project Bug tracker Changelog'),
            contact_author_url=URL('https://github.com/Aleks-Ya/note-size-anki-addon/issues')
        ),
        GithubInfo(
            github_links=[
                GitHubLink(URL('https://github.com/Aleks-Ya/note-size-anki-addon/issues'), github_user, github_repo),
                GitHubLink(URL('https://github.com/Aleks-Ya/note-size-anki-addon/blob/main/docs/user-manual.md'),
                           github_user, github_repo),
                GitHubLink(URL('https://github.com/Aleks-Ya/note-size-anki-addon'), github_user, github_repo),
                GitHubLink(URL('https://github.com/Aleks-Ya/note-size-anki-addon/issues'), github_user, github_repo),
                GitHubLink(URL('https://github.com/Aleks-Ya/note-size-anki-addon/blob/main/CHANGELOG.md'), github_user,
                           github_repo),
                GitHubLink(
                    URL('https://github.com/Aleks-Ya/note-size-anki-addon/actions/workflows/unit-tests-linux.yml'),
                    github_user, github_repo),
                GitHubLink(
                    URL('https://github.com/Aleks-Ya/note-size-anki-addon/actions/workflows/unit-tests-linux.yml/badge.svg'),
                    github_user, github_repo)
            ],
            github_repo=github_repo,
            languages=[],
            stars=0,
            last_commit=None,
            action_count=0,
            tests_count=0
        ),
        forum=AnkiForumInfo(
            anki_forum_url=URL("https://forums.ankiweb.net/t/note-size-addon-support/46001"),
            topic_slug=None,
            topic_id=None,
            last_posted_at=None,
            posts_count=None
        )
    )


def test_parse_addon_page_without_description(overrider: Overrider):
    parser: AddonPageParser = AddonPageParser(overrider)
    addon_header: AddonHeader = AddonHeader(
        id=AddonId(1),
        title=AddonTitle("No description addon"),
        addon_page_url=URL("https://ankiweb.net/shared/info/1"),
        rating=AddonRating(0),
        update_date=UpdateDate("2025-04-19"),
        anki_version=AnkiVersion("25.09.2~"))
    html: HtmlStr = HtmlStr("<html><body><main><h1>No description</h1></main></body></html>")
    addon_info: AddonInfo = parser.parse_addon_page(addon_header, html)
    assert addon_info.page.description == ""
    assert addon_info.page.description_language is None
    assert addon_info.page.description_language_confidence is None


def test_parse_addon_page_detects_non_english_description(overrider: Overrider):
    """The Spanish description is tagged with the ISO-639-1 code 'es' and a confidence value."""
    parser: AddonPageParser = AddonPageParser(overrider)
    html: HtmlStr = HtmlStr(
        '<html><body><main>'
        '<div class="shared-item-description">'
        'Este complemento muestra el tamaño de tu colección y de cada nota, incluyendo los archivos adjuntos.'
        '</div>'
        '</main></body></html>')
    addon_info: AddonInfo = parser.parse_addon_page(__header(8), html)
    assert addon_info.page.description_language == "es"
    assert addon_info.page.description_language_confidence is not None


def test_comment_github_url_does_not_override_description_repo(overrider: Overrider):
    """A repo linked (repeatedly) in a user comment must not outvote the repo from the description."""
    parser: AddonPageParser = AddonPageParser(overrider)
    addon_header: AddonHeader = AddonHeader(
        id=AddonId(2),
        title=AddonTitle("Comment pollution addon"),
        addon_page_url=URL("https://ankiweb.net/shared/info/2"),
        rating=AddonRating(0),
        update_date=UpdateDate("2025-04-19"),
        anki_version=AnkiVersion("25.09.2~"))
    html: HtmlStr = HtmlStr(
        '<html><body><main>'
        '<h2>Description</h2>'
        '<div class="shared-item-description">'
        '<a href="https://github.com/real-author/real-addon">Source</a>'
        '</div>'
        '<h2>Reviews</h2>'
        '<div class="mb-3"><a href="https://github.com/spammer/other-repo">see this</a></div>'
        '<div class="mb-3"><a href="https://github.com/spammer/other-repo">and this</a></div>'
        '<div class="mb-3"><a href="https://github.com/spammer/other-repo">and this too</a></div>'
        '</main></body></html>')
    addon_info: AddonInfo = parser.parse_addon_page(addon_header, html)
    expected_repo: GithubRepo = GithubRepo(GithubUserName("real-author"), GithubRepoName("real-addon"))
    assert addon_info.github.github_repo == expected_repo
    assert [link.url for link in addon_info.github.github_links] == [
        URL("https://github.com/real-author/real-addon")]


def __header(addon_id: int) -> AddonHeader:
    return AddonHeader(
        id=AddonId(addon_id),
        title=AddonTitle("Some addon"),
        addon_page_url=URL(f"https://ankiweb.net/shared/info/{addon_id}"),
        rating=AddonRating(0),
        update_date=UpdateDate("2025-04-19"),
        anki_version=AnkiVersion("25.09.2~"))


def test_contact_author_forum_link_wins_over_description_vote(overrider: Overrider):
    """The Contact Author button's forum URL beats a differently-voted forum URL in the description."""
    parser: AddonPageParser = AddonPageParser(overrider)
    html: HtmlStr = HtmlStr(
        '<html><body><main>'
        '<a class="btn btn-outline-primary" '
        'href="https://forums.ankiweb.net/t/review-heatmap-official-support-thread/928/1">Contact Author</a>'
        '<div class="shared-item-description">'
        '<a href="https://forums.ankiweb.net/t/some-other-thread/1">A</a>'
        '<a href="https://forums.ankiweb.net/t/some-other-thread/1">B</a>'
        '<a href="https://forums.ankiweb.net/t/some-other-thread/1">C</a>'
        '</div>'
        '</main></body></html>')
    addon_info: AddonInfo = parser.parse_addon_page(__header(3), html)
    assert addon_info.forum.anki_forum_url == URL(
        "https://forums.ankiweb.net/t/review-heatmap-official-support-thread/928/1")


def test_contact_author_github_link_wins_over_description_vote(overrider: Overrider):
    """The Contact Author button's GitHub repo beats a differently-voted repo in the description."""
    parser: AddonPageParser = AddonPageParser(overrider)
    html: HtmlStr = HtmlStr(
        '<html><body><main>'
        '<a class="btn btn-outline-primary" '
        'href="https://github.com/real-author/real-addon/issues">Contact Author</a>'
        '<div class="shared-item-description">'
        '<a href="https://github.com/other/other-repo">A</a>'
        '<a href="https://github.com/other/other-repo">B</a>'
        '<a href="https://github.com/other/other-repo">C</a>'
        '</div>'
        '</main></body></html>')
    addon_info: AddonInfo = parser.parse_addon_page(__header(4), html)
    assert addon_info.github.github_repo == GithubRepo(GithubUserName("real-author"), GithubRepoName("real-addon"))


def test_manual_override_beats_contact_author_forum_link(overrider: Overrider):
    """An overrides.yaml forum URL (addon 111623432) still wins over the Contact Author button."""
    parser: AddonPageParser = AddonPageParser(overrider)
    html: HtmlStr = HtmlStr(
        '<html><body><main>'
        '<a class="btn btn-outline-primary" '
        'href="https://forums.ankiweb.net/t/wrong-thread/999">Contact Author</a>'
        '</main></body></html>')
    addon_info: AddonInfo = parser.parse_addon_page(__header(111623432), html)
    assert addon_info.forum.anki_forum_url == URL(
        "https://forums.ankiweb.net/t/hypertts-spirtual-successor-to-awesometts/17143")


def test_ai_declaration_detected_without_github_repo(overrider: Overrider):
    """A repo-less addon that declares AI in its description still gets ai_declaration_markers."""
    parser: AddonPageParser = AddonPageParser(overrider)
    html: HtmlStr = HtmlStr(
        '<html><body><main>'
        '<div class="shared-item-description">'
        'A simple addon that was built with ChatGPT. It has no source repository.'
        '</div>'
        '</main></body></html>')
    addon_info: AddonInfo = parser.parse_addon_page(__header(6), html)
    assert addon_info.github.github_repo is None
    assert addon_info.page.ai_declaration_markers == ["chatgpt"]


def test_plain_description_has_no_ai_declaration_markers(overrider: Overrider):
    parser: AddonPageParser = AddonPageParser(overrider)
    html: HtmlStr = HtmlStr(
        '<html><body><main>'
        '<div class="shared-item-description">A handy addon for reviewing cards.</div>'
        '</main></body></html>')
    addon_info: AddonInfo = parser.parse_addon_page(__header(7), html)
    assert addon_info.page.ai_declaration_markers == []


def test_no_contact_author_button_falls_back_to_description_vote(overrider: Overrider):
    """Without a Contact Author button the forum URL still comes from the description majority vote."""
    parser: AddonPageParser = AddonPageParser(overrider)
    html: HtmlStr = HtmlStr(
        '<html><body><main>'
        '<div class="shared-item-description">'
        '<a href="https://forums.ankiweb.net/t/the-only-thread/42">Support</a>'
        '</div>'
        '</main></body></html>')
    addon_info: AddonInfo = parser.parse_addon_page(__header(5), html)
    assert addon_info.forum.anki_forum_url == URL("https://forums.ankiweb.net/t/the-only-thread/42")
