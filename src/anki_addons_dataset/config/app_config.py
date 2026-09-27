import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from anki_addons_dataset.common.log import Log

CONFIG_FILE_NAME: str = ".anki-addons-dataset.yaml"

DEFAULT_LOG_FORMAT: str = '%(asctime)-15s %(levelname)-8s [%(threadName)-10s] %(message)s'


def default_config_file() -> Path:
    """The config file used when `--config` is not given.

    Deliberately outside the working directory: the working directory is itself a
    config key, so keeping the file there would be circular."""
    return Path.home() / CONFIG_FILE_NAME


@dataclass(frozen=True)
class GithubConfig:
    token_file: Path


@dataclass(frozen=True)
class AiConfig:
    endpoint: str
    api_key_file: Path
    model: str
    readme_max_chars: int
    workers: int


@dataclass(frozen=True)
class HuggingFaceConfig:
    repo_id: str
    synced_dirs: list[str]


@dataclass(frozen=True)
class LoggingConfig:
    level: int
    format: str
    file: Optional[Path]


@dataclass(frozen=True)
class AppConfig:
    working_dir: Path
    github: GithubConfig
    ai: AiConfig
    huggingface: HuggingFaceConfig
    logging: LoggingConfig

    @staticmethod
    def defaults() -> 'AppConfig':
        """The built-in defaults, reproducing the behaviour the app had before it was configurable."""
        return AppConfig(
            working_dir=Path.home() / "anki-addons-dataset",
            github=GithubConfig(token_file=Path.home() / ".github" / "token.txt"),
            ai=AiConfig(endpoint="https://api.deepseek.com",
                        api_key_file=Path.home() / ".config" / "anki-addons-dataset" / "deepseek-api-key.txt",
                        model="deepseek-flash", readme_max_chars=8000, workers=4),
            huggingface=HuggingFaceConfig(repo_id="Ya-Alex/anki-addons", synced_dirs=["history", "latest"]),
            logging=LoggingConfig(level=logging.INFO, format=DEFAULT_LOG_FORMAT, file=None))


class ConfigLoader:
    """Reads the optional YAML config file over the built-in defaults.

    Every key is optional, but an unknown key is an error rather than a no-op: a silently
    ignored typo in a config file is the classic way to spend an hour debugging the wrong thing."""

    @staticmethod
    def load(config_file: Path) -> AppConfig:
        defaults: AppConfig = AppConfig.defaults()
        if not config_file.is_file():
            return defaults
        content: Any = yaml.safe_load(config_file.read_text())
        if content is None:
            return defaults
        raw: dict[str, Any] = ConfigLoader.__as_mapping(content, "", config_file)
        ConfigLoader.__reject_unknown(raw, ["working_dir", "github", "ai", "huggingface", "logging"], "", config_file)
        return AppConfig(
            working_dir=ConfigLoader.__path(raw, "working_dir", "", config_file, defaults.working_dir),
            github=ConfigLoader.__github(raw, config_file, defaults.github),
            ai=ConfigLoader.__ai(raw, config_file, defaults.ai),
            huggingface=ConfigLoader.__hugging_face(raw, config_file, defaults.huggingface),
            logging=ConfigLoader.__logging(raw, config_file, defaults.logging))

    @staticmethod
    def __github(raw: dict[str, Any], config_file: Path, defaults: GithubConfig) -> GithubConfig:
        section: dict[str, Any] = ConfigLoader.__section(raw, "github", config_file)
        ConfigLoader.__reject_unknown(section, ["token_file"], "github", config_file)
        return GithubConfig(
            token_file=ConfigLoader.__path(section, "token_file", "github", config_file, defaults.token_file))

    @staticmethod
    def __ai(raw: dict[str, Any], config_file: Path, defaults: AiConfig) -> AiConfig:
        section: dict[str, Any] = ConfigLoader.__section(raw, "ai", config_file)
        ConfigLoader.__reject_unknown(section, ["endpoint", "api_key_file", "model", "readme_max_chars", "workers"],
                                      "ai", config_file)
        return AiConfig(
            endpoint=ConfigLoader.__string(section, "endpoint", "ai", config_file, defaults.endpoint),
            api_key_file=ConfigLoader.__path(section, "api_key_file", "ai", config_file, defaults.api_key_file),
            model=ConfigLoader.__string(section, "model", "ai", config_file, defaults.model),
            readme_max_chars=ConfigLoader.__positive_int(section, "readme_max_chars", "ai", config_file,
                                                         defaults.readme_max_chars),
            workers=ConfigLoader.__positive_int(section, "workers", "ai", config_file, defaults.workers))

    @staticmethod
    def __hugging_face(raw: dict[str, Any], config_file: Path, defaults: HuggingFaceConfig) -> HuggingFaceConfig:
        section: dict[str, Any] = ConfigLoader.__section(raw, "huggingface", config_file)
        ConfigLoader.__reject_unknown(section, ["repo_id", "synced_dirs"], "huggingface", config_file)
        return HuggingFaceConfig(
            repo_id=ConfigLoader.__string(section, "repo_id", "huggingface", config_file, defaults.repo_id),
            synced_dirs=ConfigLoader.__strings(section, "synced_dirs", "huggingface", config_file,
                                               defaults.synced_dirs))

    @staticmethod
    def __logging(raw: dict[str, Any], config_file: Path, defaults: LoggingConfig) -> LoggingConfig:
        section: dict[str, Any] = ConfigLoader.__section(raw, "logging", config_file)
        ConfigLoader.__reject_unknown(section, ["level", "format", "file"], "logging", config_file)
        return LoggingConfig(
            level=ConfigLoader.__level(section, config_file, defaults.level),
            format=ConfigLoader.__string(section, "format", "logging", config_file, defaults.format),
            file=ConfigLoader.__optional_path(section, "file", "logging", config_file, defaults.file))

    @staticmethod
    def __level(section: dict[str, Any], config_file: Path, default: int) -> int:
        name: str = ConfigLoader.__string(section, "level", "logging", config_file, "")
        if not name:
            return default
        try:
            return Log.parse_level(name)
        except ValueError as e:
            raise ValueError(f"Invalid value for 'logging.level' in config file {config_file}: {e}") from e

    @staticmethod
    def __section(raw: dict[str, Any], key: str, config_file: Path) -> dict[str, Any]:
        if key not in raw or raw[key] is None:
            return {}
        return ConfigLoader.__as_mapping(raw[key], key, config_file)

    @staticmethod
    def __as_mapping(value: Any, key: str, config_file: Path) -> dict[str, Any]:
        if not isinstance(value, dict):
            location: str = f"'{key}'" if key else "the top level"
            raise ValueError(f"Invalid config file {config_file}: expected a mapping at {location}, "
                             f"got {type(value).__name__}")
        return value

    @staticmethod
    def __reject_unknown(section: dict[str, Any], allowed: list[str], prefix: str, config_file: Path) -> None:
        for key in section:
            if key not in allowed:
                full_key: str = f"{prefix}.{key}" if prefix else str(key)
                raise ValueError(f"Unknown key '{full_key}' in config file {config_file}. "
                                 f"Known keys here: {', '.join(allowed)}")

    @staticmethod
    def __string(section: dict[str, Any], key: str, prefix: str, config_file: Path, default: str) -> str:
        if key not in section or section[key] is None:
            return default
        value: Any = section[key]
        if not isinstance(value, str):
            raise ValueError(f"Invalid value for '{ConfigLoader.__full_key(prefix, key)}' in config file "
                             f"{config_file}: expected a string, got {type(value).__name__}")
        return value

    @staticmethod
    def __strings(section: dict[str, Any], key: str, prefix: str, config_file: Path,
                  default: list[str]) -> list[str]:
        if key not in section or section[key] is None:
            return default
        value: Any = section[key]
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"Invalid value for '{ConfigLoader.__full_key(prefix, key)}' in config file "
                             f"{config_file}: expected a list of strings")
        return value

    @staticmethod
    def __positive_int(section: dict[str, Any], key: str, prefix: str, config_file: Path, default: int) -> int:
        if key not in section or section[key] is None:
            return default
        value: Any = section[key]
        # bool is an int subclass, and `workers: true` is a typo rather than a worker count.
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"Invalid value for '{ConfigLoader.__full_key(prefix, key)}' in config file "
                             f"{config_file}: expected a positive integer")
        return value

    @staticmethod
    def __path(section: dict[str, Any], key: str, prefix: str, config_file: Path, default: Path) -> Path:
        path: Optional[Path] = ConfigLoader.__optional_path(section, key, prefix, config_file, None)
        return path if path else default

    @staticmethod
    def __optional_path(section: dict[str, Any], key: str, prefix: str, config_file: Path,
                        default: Optional[Path]) -> Optional[Path]:
        value: str = ConfigLoader.__string(section, key, prefix, config_file, "")
        if not value:
            return default
        return Path(os.path.expandvars(value)).expanduser()

    @staticmethod
    def __full_key(prefix: str, key: str) -> str:
        return f"{prefix}.{key}" if prefix else key
