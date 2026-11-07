from anki_addons_dataset.collector.url_parser import UrlParser
from anki_addons_dataset.common.data_types import URL, GithubLink, GithubRepo, GithubUser, GithubUserName, \
    GithubRepoName


def test_find_github_links():
    links: list[URL] = [
        URL("https://github.com/Aleks-Ya/note-size-anki-addon/issues"),
        URL("https://github.com/shigeyukey/AnkiRestart"),
        URL("https://ankiweb.net/logo.png"),
        URL("https://github.com/Arthur-Milchior/anki-copy-note?tab=readme-ov-file#copy-notes"),
        URL("https://github.com/kanjieater/anki-plugin-heisigs-rtk#readme"),
        URL("https://github.com/Arthur-Milchior/note-organizer)*"),
        URL("https://github.com/Glutanimate"),
        URL("https://github.com/Arthur-Milchior/")
    ]
    github_links: list[GithubLink] = UrlParser.find_github_links(links)
    assert github_links == [
        GithubLink(URL("https://github.com/Aleks-Ya/note-size-anki-addon/issues"),
                   GithubUser(GithubUserName("aleks-ya")),
                   GithubRepo(GithubUserName("aleks-ya"), GithubRepoName("note-size-anki-addon"))),
        GithubLink(URL("https://github.com/shigeyukey/AnkiRestart"),
                   GithubUser(GithubUserName("shigeyukey")),
                   GithubRepo(GithubUserName("shigeyukey"), GithubRepoName("ankirestart"))),
        GithubLink(URL("https://github.com/Arthur-Milchior/anki-copy-note?tab=readme-ov-file#copy-notes"),
                   GithubUser(GithubUserName("arthur-milchior")),
                   GithubRepo(GithubUserName("arthur-milchior"), GithubRepoName("anki-copy-note"))),
        GithubLink(URL("https://github.com/kanjieater/anki-plugin-heisigs-rtk#readme"),
                   GithubUser(GithubUserName("kanjieater")),
                   GithubRepo(GithubUserName("kanjieater"), GithubRepoName("anki-plugin-heisigs-rtk"))),
        GithubLink(URL("https://github.com/Arthur-Milchior/note-organizer)*"),
                   GithubUser(GithubUserName("arthur-milchior")),
                   GithubRepo(GithubUserName("arthur-milchior"), GithubRepoName("note-organizer"))),
        GithubLink(URL("https://github.com/Glutanimate"), GithubUser(GithubUserName("glutanimate")), None),
        GithubLink(URL("https://github.com/Arthur-Milchior/"), GithubUser(GithubUserName("arthur-milchior")), None)
    ]


def test_find_anki_forum_links():
    links: list[URL] = [
        URL("https://github.com/Aleks-Ya/note-size-anki-addon/issues"),
        URL("https://ankiweb.net/logo.png"),
        URL("https://forums.ankiweb.net/t/batch-create-filtered-decks-official-thread/545")
    ]
    anki_forum_links: list[URL] = UrlParser.find_anki_forum_links(links)
    assert anki_forum_links == [
        URL("https://forums.ankiweb.net/t/batch-create-filtered-decks-official-thread/545")
    ]
