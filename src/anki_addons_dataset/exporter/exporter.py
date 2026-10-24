from abc import abstractmethod, ABC
from pathlib import Path

from anki_addons_dataset.common.data_types import AddonInfos, DatasetSnapshotMetadata, RawMetadata, \
    AiTagDefinition, AnkiRelease


class Exporter(ABC):
    def __init__(self, final_dir: Path):
        self._final_dir: Path = final_dir
        self._final_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def export_addon_infos(self, addon_infos: AddonInfos, dataset_snapshot_metadata: DatasetSnapshotMetadata,
                           raw_metadata: RawMetadata) -> None:
        ...

    @abstractmethod
    def export_tags(self, tags: list[AiTagDefinition], dataset_snapshot_metadata: DatasetSnapshotMetadata,
                    raw_metadata: RawMetadata) -> None:
        ...

    @abstractmethod
    def export_anki_versions(self, anki_versions: list[AnkiRelease], dataset_snapshot_metadata: DatasetSnapshotMetadata,
                             raw_metadata: RawMetadata) -> None:
        ...
