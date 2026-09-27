import json
import logging
from logging import Logger
from pathlib import Path
from typing import Any, Optional

from anki_addons_dataset.common.working_dir import SnapshotDir

log: Logger = logging.getLogger(__name__)


class SampleCollector:
    __addons_key: str = "addons"

    def __init__(self, snapshot_dir: SnapshotDir) -> None:
        self.__sample_file: Path = snapshot_dir.get_sample_file()

    def set_addons(self, addons: Optional[int]) -> None:
        self.__sample_file.write_text(json.dumps({self.__addons_key: addons}, indent=2))

    def read_addons(self) -> Optional[int]:
        if not self.__sample_file.exists():
            return None
        content: dict[str, Any] = json.loads(self.__sample_file.read_text())
        return content.get(self.__addons_key)

    def effective_addons(self, configured_addons: Optional[int]) -> Optional[int]:
        """The addon limit an offline step must apply: the smaller of the configured and the recorded one."""
        recorded_addons: Optional[int] = self.read_addons()
        if recorded_addons is None:
            return configured_addons
        if configured_addons is None:
            log.info(f"Snapshot was downloaded with an addon sample of {recorded_addons}, applying it")
            return recorded_addons
        if configured_addons != recorded_addons:
            log.warning(f"Configured addon sample is {configured_addons} but the snapshot was downloaded "
                        f"with {recorded_addons}: using {min(configured_addons, recorded_addons)}")
        return min(configured_addons, recorded_addons)
