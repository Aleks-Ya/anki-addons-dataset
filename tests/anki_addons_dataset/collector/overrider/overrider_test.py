from anki_addons_dataset.collector.overrider.overrider import Overrider
from anki_addons_dataset.common.data_types import URL, GitHubLink, AddonId, GitHubUser, GithubUserName, GithubRepo, \
    GithubRepoName
from anki_addons_dataset.common.working_dir import VersionDir


def test_override_github_link(overrider: Overrider, note_size_addon_id: AddonId):
    assert overrider.override_github_link(note_size_addon_id) is None
    override_link: GitHubLink = overrider.override_github_link(AddonId(1984823157))
    github_user_name: GithubUserName = GithubUserName("r-appleton")
    assert override_link == GitHubLink(URL("https://github.com/r-appleton/addons"),
                                       GitHubUser(github_user_name),
                                       GithubRepo(github_user_name, GithubRepoName("addons")))


def test_override_anki_forum_url(overrider: Overrider, note_size_addon_id: AddonId, hyper_tts_addon_id: AddonId):
    assert overrider.override_anki_forum_url(note_size_addon_id) is None
    assert overrider.override_anki_forum_url(hyper_tts_addon_id) == URL(
        "https://forums.ankiweb.net/t/hypertts-spirtual-successor-to-awesometts/17143")


def test_copy_override_yaml_to_dataset(overrider: Overrider, version_dir: VersionDir):
    assert (version_dir.get_stage_dir() / "4-overrider" / "overrides.yaml").exists()
