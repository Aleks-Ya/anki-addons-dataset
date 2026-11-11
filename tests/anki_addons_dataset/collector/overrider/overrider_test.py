from typing import Optional

from anki_addons_dataset.collector.overrider.overrider import Overrider, ForkOverride, DuplicateOverride
from anki_addons_dataset.common.data_types import URL, GithubLink, AddonId, GithubUser, GithubUserName, GithubRepo, \
    GithubRepoName
from anki_addons_dataset.common.working_dir import SnapshotDir


def test_override_github_link(overrider: Overrider, note_size_addon_id: AddonId):
    assert overrider.override_github_link(note_size_addon_id) is None
    override_link: Optional[GithubLink] = overrider.override_github_link(AddonId(1984823157))
    github_user_name: GithubUserName = GithubUserName("r-appleton")
    assert override_link == GithubLink(URL("https://github.com/r-appleton/addons"),
                                       GithubUser(github_user_name),
                                       GithubRepo(github_user_name, GithubRepoName("addons")))


def test_override_anki_forum_url(overrider: Overrider, note_size_addon_id: AddonId, hyper_tts_addon_id: AddonId):
    assert overrider.override_anki_forum_url(note_size_addon_id) is None
    assert overrider.override_anki_forum_url(hyper_tts_addon_id) == URL(
        "https://forums.ankiweb.net/t/hypertts-spirtual-successor-to-awesometts/17143")


def test_override_same_author(overrider: Overrider, note_size_addon_id: AddonId):
    assert overrider.override_same_author(note_size_addon_id) is None
    overrider.addons_data[AddonId(1)] = {"SameAuthorAs": 2}
    assert overrider.override_same_author(AddonId(1)) == AddonId(2)


def test_override_fork_of(overrider: Overrider, note_size_addon_id: AddonId):
    assert overrider.override_fork_of(note_size_addon_id) is None
    overrider.addons_data[AddonId(1)] = {"ForkOf": 2}
    overrider.addons_data[AddonId(3)] = {"ForkOf": None}
    assert overrider.override_fork_of(AddonId(1)) == ForkOverride(AddonId(2))
    assert overrider.override_fork_of(AddonId(3)) == ForkOverride(None)


def test_override_duplicate_of(overrider: Overrider, note_size_addon_id: AddonId):
    assert overrider.override_duplicate_of(note_size_addon_id) is None
    overrider.addons_data[AddonId(1)] = {"DuplicateOf": 2}
    overrider.addons_data[AddonId(3)] = {"DuplicateOf": None}
    assert overrider.override_duplicate_of(AddonId(1)) == DuplicateOverride(AddonId(2))
    assert overrider.override_duplicate_of(AddonId(3)) == DuplicateOverride(None)


def test_is_excluded_github_repo(overrider: Overrider):
    assert overrider.is_excluded_github_repo(URL("https://github.com/ankitects/anki")) is True
    assert overrider.is_excluded_github_repo(URL("https://github.com/ankitects/anki/issues")) is True
    assert overrider.is_excluded_github_repo(URL("https://GitHub.com/MPV-player/mpv")) is True
    assert overrider.is_excluded_github_repo(URL("https://github.com/Aleks-Ya/note-size-anki-addon")) is False


def test_copy_override_yaml_to_dataset(overrider: Overrider, snapshot_dir: SnapshotDir):
    assert (snapshot_dir.get_stage_dir() / "4-overrider" / "overrides.yaml").exists()
