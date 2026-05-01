import tempfile
import textwrap
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

from seedir import seedir

from anki_addons_dataset.common.working_dir import WorkingDir
from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient
from anki_addons_dataset.initializer.working_dir_initializer import WorkingDirInitializer


def test_initialize_working_dir(working_dir: WorkingDir, working_dir_initializer: WorkingDirInitializer,
                                hugging_face_client: HuggingFaceClient):
    working_dir.get_path().rmdir()
    assert not working_dir.get_path().exists()

    raw_zip: Path = Path(tempfile.mkstemp(".zip")[1])
    exp_metadata: str = "abc"
    with ZipFile(raw_zip, "w") as zw:
        zw.writestr("raw-metadata.json", exp_metadata)

    hugging_face_client.list_version_folders = Mock(return_value=["history/2025-01-01"])
    hugging_face_client.download_file = Mock(return_value=raw_zip)

    working_dir_initializer.initialize_working_dir()

    tree: str = seedir(working_dir.get_path(), printout=False, sort=True)
    assert tree == textwrap.dedent(f"""\
                                    {working_dir.get_path().name}/
                                    └─history/
                                      └─2025-01-01/
                                        ├─1-raw/
                                        │ └─raw-metadata.json
                                        ├─2-stage/
                                        └─3-final/""")
    act_metadata_file: Path = working_dir.get_history_dir() / '2025-01-01' / '1-raw' / 'raw-metadata.json'
    assert act_metadata_file.read_text() == exp_metadata
