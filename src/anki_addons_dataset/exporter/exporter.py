from abc import abstractmethod, ABC
from pathlib import Path

from anki_addons_dataset.common.data_types import Aggregation, AddonInfos, DatasetVersionMetadata, RawMetadata


class Exporter(ABC):
    def __init__(self, final_dir: Path):
        self._final_dir: Path = final_dir
        self._final_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def export_addon_infos(self, addon_infos: AddonInfos, dataset_version_metadata: DatasetVersionMetadata,
                           raw_metadata: RawMetadata) -> None:
        ...

    @abstractmethod
    def export_aggregation(self, aggregation: Aggregation, dataset_version_metadata: DatasetVersionMetadata,
                           raw_metadata: RawMetadata) -> None:
        ...
