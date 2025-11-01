import shutil
from pathlib import Path
from typing import Any, Optional
import logging
from logging import Logger

import yaml

from anki_addons_dataset.collector.ankiweb.url_parser import UrlParser
from anki_addons_dataset.common.data_types import AddonInfo, AddonId, URL, GitHubLink
from anki_addons_dataset.common.working_dir import VersionDir

log: Logger = logging.getLogger(__name__)


class Overrider:
    __github_url_key: str = "GitHubUrl"
    __anki_forum_url_key: str = "AnkiForumUrl"

    def __init__(self, version_dir: VersionDir):
        override_file: Path = Path(__file__).parent / "overrides.yaml"
        log.info(f"Read override file: {override_file}")
        data: dict[str, dict[AddonId, Any]] = yaml.safe_load(override_file.read_text())
        self.addons_data: dict[AddonId, Any] = data.get("addons", {})
        dest_file: Path = version_dir.get_stage_dir() / "4-overrider" / "overrides.yaml"
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(override_file, dest_file)

    def override(self, addon_infos: list[AddonInfo]) -> list[AddonInfo]:
        for addon_info in addon_infos:
            if addon_info.header.id in self.addons_data:
                for key, value in self.addons_data[addon_info.header.id].items():
                    setattr(addon_info.header, key, value)
        return addon_infos

    def override_github_link(self, addon_id: AddonId) -> Optional[GitHubLink]:
        if addon_id in self.addons_data:
            addon_data: dict[str, Any] = self.addons_data[addon_id]
            if self.__github_url_key in addon_data:
                github_url: URL = addon_data[self.__github_url_key]
                return UrlParser.parse_github_url(github_url)
        return None

    def override_anki_forum_url(self, addon_id: AddonId) -> Optional[URL]:
        if addon_id in self.addons_data:
            addon_data: dict[str, Any] = self.addons_data[addon_id]
            if self.__anki_forum_url_key in addon_data:
                return addon_data[self.__anki_forum_url_key]
        return None
