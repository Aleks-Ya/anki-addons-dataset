import dataclasses
from dataclasses import replace
from typing import Any, Optional

from anki_addons_dataset.common.data_types import AddonInfos, AddonInfo, AnkiForumInfo, PostsCount, AddonManifest, \
    SpdxLicense, Topic, DependencyName, LanguageName, URL, GithubReadme, PageLink, PageLinkSection, AddonId, \
    ForkRelation, ForkEvidence
from anki_addons_dataset.exporter.json_addon_info import JsonAddonInfo


def to_dicts(addon_infos: AddonInfos) -> list[dict[str, Any]]:
    return [dataclasses.asdict(details) for details in JsonAddonInfo.addon_infos_to_json(addon_infos)]


def test_addon_infos_to_json(addon_infos: AddonInfos):
    act_json: list[dict[str, Any]] = to_dicts(addon_infos)
    assert act_json == [{'id': 1188705668,
                         'anki_web': {'addon_page_url': 'https://ankiweb.net/shared/info/1188705668',
                                      'addon_page_content': '<html><body><h1>Sample addon page content</h1></body></html>',
                                      'contact_author_url': None,
                                      'ai_declaration_markers': ['chatgpt'],
                                      'description': 'Sample addon description for full text search',
                                      'description_language': None,
                                      'description_language_confidence': None,
                                      'description_html': '<p>Sample addon <b>description</b> for full text search</p>',
                                      'description_pre_wrap': True,
                                      'other_items_count': 2,
                                      'anki_version': '25.09.2~',
                                      'anki_point_version': 250902,
                                      'anki_version_kind': 'tested',
                                      'branches': [{'max_version': '25.09.2+',
                                                    'min_version': '24.04.1',
                                                    'updated': '2023-03-15',
                                                    'min_point_version': 240401,
                                                    'max_point_version': 250902,
                                                    'max_version_kind': 'tested'}],
                                      'dislikes': 0,
                                      'likes': 0,
                                      'links': [],
                                      'title': 'NoteSize',
                                      'rating': 4,
                                      'update_date': '2023-03-15'},
                         'github': {'action_count': 5,
                                    'languages': ['Python', 'Rust'],
                                    'last_commit': '2023-03-15T12:00:00',
                                    'links': [],
                                    'repo': 'app',
                                    'stars': 3,
                                    'tests_count': 7,
                                    'user': 'John',
                                    'license': None,
                                    'forks': None,
                                    'open_issues': None,
                                    'size_kb': None,
                                    'topics': [],
                                    'repo_description': None,
                                    'homepage': None,
                                    'archived': None,
                                    'pushed_at': None,
                                    'created_at': None,
                                    'primary_language': None,
                                    'language_bytes': [],
                                    'manifest': None,
                                    'dependencies': [],
                                    'readme': None,
                                    'ai_tooling_markers': ['claude-code', 'cursor'], 'repo_source': None,
                                    'fork_source': None},
                         'forum': {'anki_forum_url': 'https://forums.ankiweb.net/t/note-size-addon-support/46001',
                                   'topic_slug': 'note-size-addon-support',
                                   'topic_id': 46001,
                                   'last_posted_at': '2023-09-10 12:00:00+00:00',
                                   'posts_count': 42, 'topic_source': 'contact_author'},
                         'ai': {'summary': 'Shows the size of the collection and of individual notes.',
                                'model': 'test-model',
                                'tags': ['statistics']},
                         'author': {'id': 1188705668, 'addon_count': 3},
                         'forked_from': None,
                         'forks': []
                         }]


def test_addon_infos_to_json_empty_forum(addon_info: AddonInfo):
    forum: Optional[AnkiForumInfo] = None
    addon_info.forum = forum
    addon_infos: AddonInfos = AddonInfos([addon_info])

    act_json: list[dict[str, Any]] = to_dicts(addon_infos)
    assert act_json == [{'id': 1188705668,
                         'anki_web': {'addon_page_url': 'https://ankiweb.net/shared/info/1188705668',
                                      'addon_page_content': '<html><body><h1>Sample addon page content</h1></body></html>',
                                      'contact_author_url': None,
                                      'ai_declaration_markers': ['chatgpt'],
                                      'description': 'Sample addon description for full text search',
                                      'description_language': None,
                                      'description_language_confidence': None,
                                      'description_html': '<p>Sample addon <b>description</b> for full text search</p>',
                                      'description_pre_wrap': True,
                                      'other_items_count': 2,
                                      'anki_version': '25.09.2~',
                                      'anki_point_version': 250902,
                                      'anki_version_kind': 'tested',
                                      'branches': [{'max_version': '25.09.2+',
                                                    'min_version': '24.04.1',
                                                    'updated': '2023-03-15',
                                                    'min_point_version': 240401,
                                                    'max_point_version': 250902,
                                                    'max_version_kind': 'tested'}],
                                      'dislikes': 0,
                                      'likes': 0,
                                      'links': [],
                                      'title': 'NoteSize',
                                      'rating': 4,
                                      'update_date': '2023-03-15'},
                         'github': {'action_count': 5,
                                    'languages': ['Python', 'Rust'],
                                    'last_commit': '2023-03-15T12:00:00',
                                    'links': [],
                                    'repo': 'app',
                                    'stars': 3,
                                    'tests_count': 7,
                                    'user': 'John',
                                    'license': None,
                                    'forks': None,
                                    'open_issues': None,
                                    'size_kb': None,
                                    'topics': [],
                                    'repo_description': None,
                                    'homepage': None,
                                    'archived': None,
                                    'pushed_at': None,
                                    'created_at': None,
                                    'primary_language': None,
                                    'language_bytes': [],
                                    'manifest': None,
                                    'dependencies': [],
                                    'readme': None,
                                    'ai_tooling_markers': ['claude-code', 'cursor'], 'repo_source': None,
                                    'fork_source': None},
                         'forum': None,
                         'ai': {'summary': 'Shows the size of the collection and of individual notes.',
                                'model': 'test-model',
                                'tags': ['statistics']},
                         'author': {'id': 1188705668, 'addon_count': 3},
                         'forked_from': None,
                         'forks': []}]


def test_addon_infos_to_json_empty_posts_count(addon_info: AddonInfo):
    posts_count: Optional[PostsCount] = None
    addon_info.forum.posts_count = posts_count
    addon_infos: AddonInfos = AddonInfos([addon_info])

    act_json: list[dict[str, Any]] = to_dicts(addon_infos)
    assert act_json == [{'id': 1188705668,
                         'anki_web': {'addon_page_url': 'https://ankiweb.net/shared/info/1188705668',
                                      'addon_page_content': '<html><body><h1>Sample addon page content</h1></body></html>',
                                      'contact_author_url': None,
                                      'ai_declaration_markers': ['chatgpt'],
                                      'description': 'Sample addon description for full text search',
                                      'description_language': None,
                                      'description_language_confidence': None,
                                      'description_html': '<p>Sample addon <b>description</b> for full text search</p>',
                                      'description_pre_wrap': True,
                                      'other_items_count': 2,
                                      'anki_version': '25.09.2~',
                                      'anki_point_version': 250902,
                                      'anki_version_kind': 'tested',
                                      'branches': [{'max_version': '25.09.2+',
                                                    'min_version': '24.04.1',
                                                    'updated': '2023-03-15',
                                                    'min_point_version': 240401,
                                                    'max_point_version': 250902,
                                                    'max_version_kind': 'tested'}],
                                      'dislikes': 0,
                                      'likes': 0,
                                      'links': [],
                                      'title': 'NoteSize',
                                      'rating': 4,
                                      'update_date': '2023-03-15'},
                         'github': {'action_count': 5,
                                    'languages': ['Python', 'Rust'],
                                    'last_commit': '2023-03-15T12:00:00',
                                    'links': [],
                                    'repo': 'app',
                                    'stars': 3,
                                    'tests_count': 7,
                                    'user': 'John',
                                    'license': None,
                                    'forks': None,
                                    'open_issues': None,
                                    'size_kb': None,
                                    'topics': [],
                                    'repo_description': None,
                                    'homepage': None,
                                    'archived': None,
                                    'pushed_at': None,
                                    'created_at': None,
                                    'primary_language': None,
                                    'language_bytes': [],
                                    'manifest': None,
                                    'dependencies': [],
                                    'readme': None,
                                    'ai_tooling_markers': ['claude-code', 'cursor'], 'repo_source': None,
                                    'fork_source': None},
                         'forum': {'anki_forum_url': 'https://forums.ankiweb.net/t/note-size-addon-support/46001',
                                   'topic_slug': 'note-size-addon-support',
                                   'topic_id': 46001,
                                   'last_posted_at': '2023-09-10 12:00:00+00:00',
                                   'posts_count': None, 'topic_source': 'contact_author'},
                         'ai': {'summary': 'Shows the size of the collection and of individual notes.',
                                'model': 'test-model',
                                'tags': ['statistics']},
                         'author': {'id': 1188705668, 'addon_count': 3},
                         'forked_from': None,
                         'forks': []}]


def test_addon_infos_to_json_empty_last_posted_at(addon_info: AddonInfo):
    addon_info.forum.last_posted_at = None
    addon_infos: AddonInfos = AddonInfos([addon_info])

    act_json: list[dict[str, Any]] = to_dicts(addon_infos)
    assert act_json[0]['forum'] == {'anki_forum_url': 'https://forums.ankiweb.net/t/note-size-addon-support/46001',
                                    'topic_slug': 'note-size-addon-support',
                                    'topic_id': 46001,
                                    'last_posted_at': None,
                                    'posts_count': 42, 'topic_source': 'contact_author'}


def test_addon_infos_to_json_with_enrichment_fields(addon_info: AddonInfo):
    # Populates every enrichment field so the exported JSON is validated against schema.json with real data.
    assert addon_info.github is not None
    addon_info.github.license = SpdxLicense("MIT")
    addon_info.github.forks = 4
    addon_info.github.topics = [Topic("anki")]
    addon_info.github.homepage = URL("https://example.com")
    addon_info.github.archived = False
    addon_info.github.language_bytes = {LanguageName("Python"): 5, LanguageName("Rust"): 2}
    addon_info.github.primary_language = LanguageName("Python")
    addon_info.github.manifest = AddonManifest(package="note_size", name="Note Size", conflicts=["123"],
                                               min_point_version=45, max_point_version=-250900,
                                               homepage="https://example.com", mod=1678900000)
    addon_info.github.dependencies = [DependencyName("requests")]
    addon_info.github.readme = GithubReadme("# NoteSize")
    addon_info.page.links = [
        PageLink(URL("https://forums.ankiweb.net/t/support/1"), PageLinkSection.DESCRIPTION, 2, ["Forum", "Support"]),
        PageLink(URL("https://github.com/u/r/issues"), PageLinkSection.CONTACT_AUTHOR, 1, ["Contact Author"])]

    act_json: dict[str, Any] = to_dicts(AddonInfos([addon_info]))[0]
    assert act_json["anki_web"]["links"] == [
        {"url": "https://forums.ankiweb.net/t/support/1", "section": "description", "count": 2,
         "texts": ["Forum", "Support"]},
        {"url": "https://github.com/u/r/issues", "section": "contact_author", "count": 1, "texts": ["Contact Author"]}]
    assert act_json["anki_web"]["contact_author_url"] == "https://github.com/u/r/issues"
    github: dict[str, Any] = act_json["github"]
    assert github["license"] == "MIT"
    assert github["topics"] == ["anki"]
    assert github["primary_language"] == "Python"
    assert github["language_bytes"] == [{"name": "Python", "bytes": 5}, {"name": "Rust", "bytes": 2}]
    assert github["manifest"]["package"] == "note_size"
    assert github["manifest"]["min_version"] == "2.1.45"
    assert github["manifest"]["max_version"] == "25.09"
    assert github["manifest"]["max_version_kind"] == "hard"
    assert github["dependencies"] == ["requests"]
    assert github["readme"] == "# NoteSize"



def test_addon_infos_to_json_one_parent_with_several_forks(addon_info: AddonInfo):
    def addon(addon_id: int, forked_from: Optional[ForkRelation]) -> AddonInfo:
        return replace(addon_info, header=replace(addon_info.header, id=AddonId(addon_id)), forked_from=forked_from)

    act_json: list[dict[str, Any]] = to_dicts(AddonInfos([
        addon(10, None),
        addon(20, ForkRelation(AddonId(10), ForkEvidence.GITHUB_FORK)),
        addon(30, ForkRelation(AddonId(10), ForkEvidence.AI))]))
    assert [(item["id"], item["forked_from"], item["forks"]) for item in act_json] == [
        (10, None, [20, 30]),
        (20, {"id": 10, "evidence": "github_fork"}, []),
        (30, {"id": 10, "evidence": "ai"}, [])]
