import json
from datetime import date, datetime
from pathlib import Path

from anki_addons_dataset.common.data_types import AddonInfo, AddonInfos, AddonHeader, AddonPage, AddonBranch, \
    GithubInfo, GitHubLink, GitHubUser, GithubRepo, AnkiForumInfo, AddonId, AnkiVersion, HtmlStr, URL, \
    GithubUserName, GithubRepoName, LanguageName, ScriptVersion, AddonRating, UpdateDate, AddonTitle, \
    AddonManifest, SpdxLicense, Topic, DependencyName
from anki_addons_dataset.common.json_helper import JsonHelper


def test_addon_infos_dump_round_trip(addon_infos: AddonInfos, script_version: ScriptVersion, working_dir_path: Path):
    dump_file: Path = working_dir_path / "addon-infos.json"

    JsonHelper.write_addon_infos_dump(addon_infos, script_version, dump_file)
    read_script_version, read_addon_infos = JsonHelper.read_addon_infos_dump(dump_file)

    assert read_script_version == script_version
    assert read_addon_infos == addon_infos


def test_addon_infos_dump_round_trip_with_none_fields(script_version: ScriptVersion, working_dir_path: Path):
    addon_info: AddonInfo = AddonInfo(
        header=AddonHeader(id=AddonId(1), title=AddonTitle("No GitHub"), addon_page_url=URL("https://ankiweb.net/shared/info/1"),
                           rating=AddonRating(0), update_date=UpdateDate("2024-01-01"), anki_version=AnkiVersion("24.04.1")),
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
    assert github is not None
    assert isinstance(github.last_commit, datetime)


def test_addon_infos_dump_round_trip_with_enrichment_fields(addon_info: AddonInfo, script_version: ScriptVersion,
                                                            working_dir_path: Path):
    assert addon_info.github is not None
    addon_info.github.license = SpdxLicense("MIT")
    addon_info.github.forks = 4
    addon_info.github.open_issues = 2
    addon_info.github.size_kb = 128
    addon_info.github.topics = [Topic("anki"), Topic("flashcards")]
    addon_info.github.repo_description = "A NoteSize addon"
    addon_info.github.homepage = URL("https://example.com")
    addon_info.github.archived = False
    addon_info.github.pushed_at = datetime(2023, 3, 16, 10, 0, 0)
    addon_info.github.created_at = datetime(2020, 1, 1, 9, 0, 0)
    addon_info.github.primary_language = LanguageName("Python")
    addon_info.github.language_bytes = {LanguageName("Python"): 5, LanguageName("Rust"): 2}
    addon_info.github.manifest = AddonManifest(package="note_size", name="Note Size", conflicts=["123"],
                                               min_point_version=45, max_point_version=None,
                                               homepage="https://example.com", mod=1678900000)
    addon_info.github.dependencies = [DependencyName("requests"), DependencyName("beautifulsoup4")]
    addon_info.github.readme = "# NoteSize"
    addon_info.github.ai_tooling_markers = ["claude-code", "cursor"]
    addon_infos: AddonInfos = AddonInfos([addon_info])
    dump_file: Path = working_dir_path / "addon-infos.json"

    JsonHelper.write_addon_infos_dump(addon_infos, script_version, dump_file)
    _, read_addon_infos = JsonHelper.read_addon_infos_dump(dump_file)

    assert read_addon_infos == addon_infos


def test_addon_infos_dump_reads_legacy_dump_without_enrichment_fields(addon_infos: AddonInfos,
                                                                     script_version: ScriptVersion,
                                                                     working_dir_path: Path):
    # An older dump has no enrichment keys in `github`; reading must default them rather than raise.
    dump_file: Path = working_dir_path / "addon-infos.json"
    JsonHelper.write_addon_infos_dump(addon_infos, script_version, dump_file)
    envelope: dict = json.loads(dump_file.read_text())
    legacy_keys = ["license", "forks", "open_issues", "size_kb", "topics", "repo_description", "homepage",
                   "archived", "pushed_at", "created_at", "primary_language", "language_bytes", "manifest",
                   "dependencies", "readme", "ai_tooling_markers"]
    for key in legacy_keys:
        envelope["addon_infos"][0]["github"].pop(key, None)
    dump_file.write_text(json.dumps(envelope))

    _, read_addon_infos = JsonHelper.read_addon_infos_dump(dump_file)

    github = read_addon_infos[0].github
    assert github is not None
    assert github.license is None
    assert github.topics == []
    assert github.language_bytes == {}
    assert github.manifest is None
    assert github.dependencies == []
    assert github.readme is None
    assert github.ai_tooling_markers == []
    forum = read_addon_infos[0].forum
    assert forum is not None
    assert isinstance(forum.last_posted_at, datetime)
