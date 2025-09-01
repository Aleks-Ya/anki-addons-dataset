import datetime
from pathlib import Path

from anki_addons_dataset.collector.ankiweb.addon_page_parser import AddonPageParser
from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import AddonHeader, AddonInfo, AddonPage, GithubInfo, AddonId, GitHubLink, \
    URL, GitHubUser, GitHubRepo, GithubUserName, GithubRepoName, Version, HtmlStr


def test_parse_addon_page(overrider: Overrider):
    addon_html_file: Path = Path(__file__).parent / "1188705668.html"
    addon_html: HtmlStr = HtmlStr(addon_html_file.read_text())
    parser: AddonPageParser = AddonPageParser(overrider)
    addon_header: AddonHeader = AddonHeader(
        id=AddonId(1188705668),
        name="Note Size - sort notes by size and see collection size",
        addon_page="https://ankiweb.net/shared/info/1188705668",
        rating=12,
        update_date="2025-04-19",
        versions="24.04.1-25.02.1+ (Updated 2025-04-19) ")
    addon_info: AddonInfo = parser.parse_addon_page(addon_header, addon_html)
    github_user: GitHubUser = GitHubUser(GithubUserName("aleks-ya"))
    github_repo: GitHubRepo = GitHubRepo(GithubUserName("aleks-ya"), GithubRepoName("note-size-anki-addon"))
    assert addon_info == AddonInfo(
        addon_header,
        AddonPage(
            like_number=12,
            dislike_number=0,
            versions=[Version(min_version='24.04.1', max_version='25.02.1+', updated=datetime.date(2025, 4, 19))],
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
                URL('https://github.com/Aleks-Ya/note-size-anki-addon/issues'),
                URL('https://raw.githubusercontent.com/Aleks-Ya/note-size-anki-addon/main/docs/images/collection-size.png'),
                URL('https://raw.githubusercontent.com/Aleks-Ya/note-size-anki-addon/main/docs/images/note-size-in-browser.png'),
                URL('https://raw.githubusercontent.com/Aleks-Ya/note-size-anki-addon/main/docs/images/sort-notes-by-size.png'),
                URL('https://raw.githubusercontent.com/Aleks-Ya/note-size-anki-addon/main/docs/images/notes-size.png'),
                URL('https://raw.githubusercontent.com/Aleks-Ya/note-size-anki-addon/main/docs/images/deck-size.png'),
                URL('https://raw.githubusercontent.com/Aleks-Ya/note-size-anki-addon/main/docs/images/add-note.png'),
                URL('https://raw.githubusercontent.com/Aleks-Ya/note-size-anki-addon/main/docs/images/open-config.png'),
                URL('https://forums.ankiweb.net/t/note-size-addon-support/46001'),
                URL('https://github.com/Aleks-Ya/note-size-anki-addon/issues'),
                URL('https://forums.ankiweb.net/t/note-size-addon-support/46001'),
                URL('https://forums.ankiweb.net/t/note-size-addon-support/46001'),
                URL('https://github.com/Aleks-Ya/note-size-anki-addon/blob/main/docs/user-manual.md'),
                URL('https://forums.ankiweb.net/t/note-size-addon-support/46001'),
                URL('https://github.com/Aleks-Ya/note-size-anki-addon'),
                URL('https://github.com/Aleks-Ya/note-size-anki-addon/issues'),
                URL('https://github.com/Aleks-Ya/note-size-anki-addon/blob/main/CHANGELOG.md'),
                URL('https://github.com/Aleks-Ya/note-size-anki-addon/actions/workflows/unit-tests-linux.yml'),
                URL('https://github.com/Aleks-Ya/note-size-anki-addon/actions/workflows/unit-tests-linux.yml/badge.svg'),
                URL('https://sonarcloud.io/summary/new_code?id=Aleks-Ya_note-size-anki-addon'),
                URL('https://sonarcloud.io/api/project_badges/measure?project=Aleks-Ya_note-size-anki-addon&amp;metric=alert_status'),
                URL('https://sonarcloud.io/summary/new_code?id=Aleks-Ya_note-size-anki-addon'),
                URL('https://sonarcloud.io/api/project_badges/measure?project=Aleks-Ya_note-size-anki-addon&amp;metric=coverage'),
                URL('https://github.com/Aleks-Ya/note-size-anki-addon/issues'),
                URL('https://ankiweb.net/shared/info/1151815987'),
                URL('https://github.com/Aleks-Ya/note-size-anki-addon/blob/main/description/configuration.md#logging-level'),
                URL('https://apps.ankiweb.net')
            ],
            anki_forum_url=URL("https://forums.ankiweb.net/t/note-size-addon-support/46001")
        ),
        GithubInfo(
            github_links=[
                GitHubLink(URL('https://github.com/Aleks-Ya/note-size-anki-addon/issues'), github_user, github_repo),
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
                    github_user, github_repo),
                GitHubLink(URL('https://github.com/Aleks-Ya/note-size-anki-addon/issues'), github_user, github_repo),
                GitHubLink(
                    URL('https://github.com/Aleks-Ya/note-size-anki-addon/blob/main/description/configuration.md#logging-level'),
                    github_user, github_repo)
            ],
            github_repo=github_repo,
            languages=[],
            stars=0,
            last_commit=None,
            action_count=0,
            tests_count=0
        )
    )
