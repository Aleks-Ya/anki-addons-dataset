from datetime import date
import textwrap

from seedir import seedir

from anki_addons_dataset.bundle.dataset_bundle import DatasetBundle
from anki_addons_dataset.common.working_dir import WorkingDir, VersionDir
from anki_addons_dataset.facade.raw_metadata import RawMetadata



def test_parse_creation_date(working_dir: WorkingDir):
    version_dir_1: VersionDir = working_dir.get_version_dir(date.fromisoformat("2025-01-01")).create()
    version_dir_1.get_metadata_json().touch()
    raw_metadata_1: RawMetadata = RawMetadata(version_dir_1)
    raw_metadata_1.set_script_version("v0.0.1")

    version_dir_2: VersionDir = working_dir.get_version_dir(date.fromisoformat("2025-01-02")).create()
    version_dir_2.get_metadata_json().touch()
    raw_metadata_2: RawMetadata = RawMetadata(version_dir_2)
    raw_metadata_2.set_script_version("v0.0.1")

    assert not working_dir.get_bundle_dir().exists()
    dataset_bundle: DatasetBundle = DatasetBundle(working_dir)
    dataset_bundle.create_bundle()
    tree: str = seedir(working_dir.get_bundle_dir(), printout=False, sort=True)
    assert tree == textwrap.dedent("""\
                                bundle/
                                ├─README.md
                                ├─history/
                                │ ├─2025-01-01/
                                │ │ ├─raw.zip
                                │ │ └─stage.zip
                                │ └─2025-01-02/
                                │   ├─raw.zip
                                │   └─stage.zip
                                └─latest/
                                  └─metadata.json""")
