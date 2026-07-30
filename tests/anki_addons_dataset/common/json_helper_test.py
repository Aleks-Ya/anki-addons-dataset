from datetime import date, datetime
from pathlib import Path

from anki_addons_dataset.common.data_types import AddonInfo, AddonInfos, AddonHeader, AddonPage, AddonBranch, \
    GithubInfo, GitHubLink, GitHubUser, GithubRepo, AnkiForumInfo, AddonId, AnkiVersion, HtmlStr, URL, \
    GithubUserName, GithubRepoName, LanguageName, ScriptVersion, Rating, UpdateDate
from anki_addons_dataset.common.json_helper import JsonHelper


def test_addon_infos_dump_round_trip(addon_infos: AddonInfos, script_version: ScriptVersion, working_dir_path: Path):
    dump_file: Path = working_dir_path / "addon-infos.json"

    JsonHelper.write_addon_infos_dump(addon_infos, script_version, dump_file)
    read_script_version, read_addon_infos = JsonHelper.read_addon_infos_dump(dump_file)

    assert read_script_version == script_version
    assert read_addon_infos == addon_infos


def test_addon_infos_dump_round_trip_with_none_fields(script_version: ScriptVersion, working_dir_path: Path):
    addon_info: AddonInfo = AddonInfo(
        header=AddonHeader(id=AddonId(1), title="No GitHub", addon_page_url=URL("https://ankiweb.net/shared/info/1"),
                           rating=Rating(0), update_date=UpdateDate("2024-01-01"), anki_version=AnkiVersion("24.04.1")),
        page=AddonPage(
            content=HtmlStr("<html></html>"), like_number=0, dislike_number=0,
            branches=[AddonBranch(min_anki_version=AnkiVersion("24.04.1"), max_anki_version=None,
                                  updated=date(2024, 1, 1))],
            other_links=[URL("https://example.com")]),
        github=GithubInfo(
            github_links=[GitHubLink(url=URL("https://github.com/u/r"),
                                     user=GitHubUser(user_name=GithubUserName("u")),
                                     repo=GithubRepo(GithubUserName("u"), GithubRepoName("r")))],
            github_repo=None, languages=[LanguageName("Python")], stars=0,
            last_commit=None, action_count=None, tests_count=None),
        forum=None,
    )
    addon_infos: AddonInfos = AddonInfos([addon_info])
    dump_file: Path = working_dir_path / "addon-infos.json"

    JsonHelper.write_addon_infos_dump(addon_infos, script_version, dump_file)
    _, read_addon_infos = JsonHelper.read_addon_infos_dump(dump_file)

    assert read_addon_infos == addon_infos
    assert read_addon_infos[0].github is not None
    assert read_addon_infos[0].github.github_repo is None
    assert read_addon_infos[0].forum is None
    assert read_addon_infos[0].page.branches[0].max_anki_version is None
    assert isinstance(read_addon_infos[0].page.branches[0].updated, date)


def test_addon_infos_dump_parses_datetimes(addon_infos: AddonInfos, script_version: ScriptVersion,
                                           working_dir_path: Path):
    dump_file: Path = working_dir_path / "addon-infos.json"

    JsonHelper.write_addon_infos_dump(addon_infos, script_version, dump_file)
    _, read_addon_infos = JsonHelper.read_addon_infos_dump(dump_file)

    github = read_addon_infos[0].github
    assert github is not None and isinstance(github.last_commit, datetime)
    forum = read_addon_infos[0].forum
    assert forum is not None and isinstance(forum.last_posted_at, datetime)
