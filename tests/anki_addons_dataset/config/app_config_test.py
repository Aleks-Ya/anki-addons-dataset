import logging
from dataclasses import replace
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from anki_addons_dataset.config.app_config import AppConfig, AiConfig, ConfigLoader, DEFAULT_LOG_FORMAT, \
    GithubConfig, HuggingFaceConfig, LoggingConfig, SampleConfig, default_config_file


def __write(tmp_path: Path, content: str) -> Path:
    config_file: Path = tmp_path / "config.yaml"
    config_file.write_text(content)
    return config_file


def test_default_config_file_sits_outside_the_working_dir(tmp_path: Path, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    # The working dir is itself a config key, so the config file must not live inside it.
    assert default_config_file() == tmp_path / ".anki-addons-dataset.yaml"
    assert default_config_file().parent != AppConfig.defaults().working_dir


def test_missing_file_yields_defaults(tmp_path: Path, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    config: AppConfig = ConfigLoader.load(tmp_path / "absent.yaml")
    assert config == AppConfig.defaults()
    assert config.working_dir == tmp_path / "anki-addons-dataset"
    assert config.github.token_file == tmp_path / ".github" / "token.txt"
    assert config.huggingface.repo_id == "Ya-Alex/anki-addons"
    assert config.huggingface.synced_dirs == ["history", "latest"]
    assert config.logging.level == logging.INFO
    assert config.logging.format == DEFAULT_LOG_FORMAT
    assert config.logging.file is None


def test_empty_file_yields_defaults(tmp_path: Path, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert ConfigLoader.load(__write(tmp_path, "")) == AppConfig.defaults()


def test_full_file_overrides_every_field(tmp_path: Path):
    config_file: Path = __write(tmp_path, """
working_dir: /data/anki
github:
  token_file: /secrets/gh.txt
ai:
  endpoint: https://ai.example.com
  api_key_file: /secrets/ai.txt
  model: some-model
  readme_max_chars: 1234
  workers: 3
huggingface:
  repo_id: Someone/scratch
  synced_dirs: [history]
logging:
  level: DEBUG
  format: '%(message)s'
  file: /var/log/anki.log
sample:
  addons: 20
  snapshots: 2
""")
    config: AppConfig = ConfigLoader.load(config_file)
    assert config == AppConfig(
        working_dir=Path("/data/anki"),
        github=GithubConfig(token_file=Path("/secrets/gh.txt")),
        ai=AiConfig(endpoint="https://ai.example.com", api_key_file=Path("/secrets/ai.txt"), model="some-model",
                    readme_max_chars=1234, workers=3),
        huggingface=HuggingFaceConfig(repo_id="Someone/scratch", synced_dirs=["history"]),
        logging=LoggingConfig(level=logging.DEBUG, format="%(message)s", file=Path("/var/log/anki.log")),
        sample=SampleConfig(addons=20, snapshots=2))


def test_partial_file_leaves_the_rest_at_defaults(tmp_path: Path, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    config_file: Path = __write(tmp_path, "huggingface:\n  repo_id: Someone/scratch\n")
    config: AppConfig = ConfigLoader.load(config_file)
    defaults: AppConfig = AppConfig.defaults()
    assert config.huggingface.repo_id == "Someone/scratch"
    assert config.huggingface.synced_dirs == defaults.huggingface.synced_dirs
    assert config.working_dir == defaults.working_dir
    assert config.github == defaults.github
    assert config.ai == defaults.ai
    assert config.logging == defaults.logging
    assert config.sample == defaults.sample


def test_paths_expand_tilde_and_env_vars(tmp_path: Path, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("HOME", str(tmp_path))  # drives both Path.home() and Path.expanduser()
    monkeypatch.setenv("ANKI_DATA", "/mnt/data")
    config_file: Path = __write(tmp_path, "working_dir: ~/datasets/anki\ngithub:\n  token_file: $ANKI_DATA/gh.txt\n")
    config: AppConfig = ConfigLoader.load(config_file)
    assert config.working_dir == tmp_path / "datasets" / "anki"
    assert config.github.token_file == Path("/mnt/data/gh.txt")


def test_unknown_top_level_key_is_rejected(tmp_path: Path):
    config_file: Path = __write(tmp_path, "workingdir: /data/anki\n")
    with pytest.raises(ValueError, match="Unknown key 'workingdir'"):
        ConfigLoader.load(config_file)


def test_unknown_nested_key_is_rejected(tmp_path: Path):
    config_file: Path = __write(tmp_path, "logging:\n  lvl: DEBUG\n")
    with pytest.raises(ValueError, match="Unknown key 'logging.lvl'"):
        ConfigLoader.load(config_file)


def test_unknown_ai_key_is_rejected(tmp_path: Path):
    config_file: Path = __write(tmp_path, "ai:\n  modell: some-model\n")
    with pytest.raises(ValueError, match="Unknown key 'ai.modell'"):
        ConfigLoader.load(config_file)


@pytest.mark.parametrize("value", ["0", "-1", "abc", "true"])
def test_non_positive_ai_worker_count_is_rejected(tmp_path: Path, value: str):
    config_file: Path = __write(tmp_path, f"ai:\n  workers: {value}\n")
    with pytest.raises(ValueError, match="Invalid value for 'ai.workers'"):
        ConfigLoader.load(config_file)


def test_invalid_log_level_is_rejected(tmp_path: Path):
    config_file: Path = __write(tmp_path, "logging:\n  level: NOPE\n")
    with pytest.raises(ValueError, match="Invalid value for 'logging.level'"):
        ConfigLoader.load(config_file)


def test_non_mapping_top_level_is_rejected(tmp_path: Path):
    config_file: Path = __write(tmp_path, "- working_dir: /data/anki\n")
    with pytest.raises(ValueError, match="expected a mapping at the top level"):
        ConfigLoader.load(config_file)


def test_non_mapping_section_is_rejected(tmp_path: Path):
    config_file: Path = __write(tmp_path, "github: /secrets/gh.txt\n")
    with pytest.raises(ValueError, match="expected a mapping at 'github'"):
        ConfigLoader.load(config_file)


def test_wrong_scalar_type_is_rejected(tmp_path: Path):
    config_file: Path = __write(tmp_path, "huggingface:\n  repo_id: 42\n")
    with pytest.raises(ValueError, match="'huggingface.repo_id'"):
        ConfigLoader.load(config_file)


def test_wrong_list_type_is_rejected(tmp_path: Path):
    config_file: Path = __write(tmp_path, "huggingface:\n  synced_dirs: history\n")
    with pytest.raises(ValueError, match="expected a list of strings"):
        ConfigLoader.load(config_file)


def test_explicit_nulls_fall_back_to_defaults(tmp_path: Path, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    config_file: Path = __write(tmp_path, "working_dir: null\ngithub: null\nlogging:\n  level: null\n  file: null\n")
    assert ConfigLoader.load(config_file) == AppConfig.defaults()


def test_working_dir_override_replaces_only_the_working_dir(tmp_path: Path, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    defaults: AppConfig = AppConfig.defaults()
    config: AppConfig = defaults.with_working_dir(Path("/data/anki"))
    assert config.working_dir == Path("/data/anki")
    assert config == replace(defaults, working_dir=Path("/data/anki"))


def test_absent_working_dir_override_keeps_the_config(tmp_path: Path, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    defaults: AppConfig = AppConfig.defaults()
    assert defaults.with_working_dir(None) == defaults


def test_sample_is_absent_by_default(tmp_path: Path, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    config: AppConfig = ConfigLoader.load(__write(tmp_path, "sample:\n"))
    assert config.sample == SampleConfig(addons=None, snapshots=None)
    assert not config.sample.is_active()


def test_sample_accepts_one_axis_alone(tmp_path: Path, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    config: AppConfig = ConfigLoader.load(__write(tmp_path, "sample:\n  addons: 5\n"))
    assert config.sample == SampleConfig(addons=5, snapshots=None)
    assert config.sample.is_active()


def test_unknown_sample_key_is_rejected(tmp_path: Path):
    config_file: Path = __write(tmp_path, "sample:\n  addon: 5\n")
    with pytest.raises(ValueError, match="Unknown key 'sample.addon'"):
        ConfigLoader.load(config_file)


@pytest.mark.parametrize("value", ["0", "-1", "true", "'5'"])
def test_invalid_sample_size_is_rejected(tmp_path: Path, value: str):
    config_file: Path = __write(tmp_path, f"sample:\n  addons: {value}\n")
    with pytest.raises(ValueError, match="Invalid value for 'sample.addons'"):
        ConfigLoader.load(config_file)


def test_with_sample_overrides_each_value_separately():
    config: AppConfig = replace(AppConfig.defaults(), sample=SampleConfig(addons=5, snapshots=2))
    assert config.with_sample(None, None) is config  # nothing passed: the file's values stand
    assert config.with_sample(7, None).sample == SampleConfig(addons=7, snapshots=2)
    assert config.with_sample(None, 3).sample == SampleConfig(addons=5, snapshots=3)


def test_with_sample_on_an_unsampled_config():
    defaults: AppConfig = AppConfig.defaults()
    assert defaults.with_sample(None, None) is defaults
    assert defaults.with_sample(20, None).sample == SampleConfig(addons=20, snapshots=None)
