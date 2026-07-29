from pathlib import Path
from unittest.mock import Mock

import pytest
from huggingface_hub import HfApi, RepoFile, RepoFolder
from huggingface_hub.errors import RepositoryNotFoundError

from anki_addons_dataset.huggingface.hugging_face_client import HuggingFaceClient


def __repo_file(path: str) -> RepoFile:
    entry: RepoFile = Mock(spec=RepoFile)
    entry.path = path
    return entry


def __build_bundle(bundle_dir: Path) -> None:
    history: Path = bundle_dir / "history" / "2026-01-01"
    history.mkdir(parents=True)
    (history / "raw.zip").write_text("raw")
    (history / "addons.parquet").write_text("parquet")
    latest: Path = bundle_dir / "latest"
    latest.mkdir(parents=True)
    (latest / "addons.parquet").write_text("parquet")


def test_upload_dataset_verifies_access_then_uploads(tmp_path: Path):
    api: HfApi = Mock(spec=HfApi)
    client: HuggingFaceClient = HuggingFaceClient(api)

    client.upload_dataset(tmp_path)

    api.auth_check.assert_called_once()
    assert api.auth_check.call_args.kwargs["write"] is True
    api.upload_large_folder.assert_called_once()
    # Access is verified before any upload happens.
    assert api.method_calls[0][0] == "auth_check"


def test_upload_dataset_raises_permission_error_when_unauthorized(tmp_path: Path):
    api: HfApi = Mock(spec=HfApi)
    response: Mock = Mock()
    response.status_code = 401
    api.auth_check.side_effect = RepositoryNotFoundError("nope", response=response)
    client: HuggingFaceClient = HuggingFaceClient(api)

    with pytest.raises(PermissionError):
        client.upload_dataset(tmp_path)

    api.upload_large_folder.assert_not_called()


def test_prune_orphans_deletes_only_files_absent_locally(tmp_path: Path):
    __build_bundle(tmp_path)
    api: HfApi = Mock(spec=HfApi)
    history_tree = [
        __repo_file("history/2026-01-01/raw.zip"),        # kept
        __repo_file("history/2026-01-01/addons.parquet"),  # kept
        __repo_file("history/2026-01-01/addons.xlsx"),     # orphan: removed locally
        __repo_file("history/2025-12-31/raw.zip"),         # orphan: snapshot removed locally
        Mock(spec=RepoFolder),                              # folders are ignored
    ]
    latest_tree = [
        __repo_file("latest/addons.parquet"),  # kept
        __repo_file("latest/addons.xlsx"),      # orphan: removed locally
    ]
    api.list_repo_tree.side_effect = [history_tree, latest_tree]
    client: HuggingFaceClient = HuggingFaceClient(api)

    client.prune_orphans(tmp_path)

    api.delete_files.assert_called_once()
    deleted: set[str] = set(api.delete_files.call_args.kwargs["delete_patterns"])
    assert deleted == {
        "history/2026-01-01/addons.xlsx",
        "history/2025-12-31/raw.zip",
        "latest/addons.xlsx",
    }


def test_prune_orphans_no_op_when_nothing_stale(tmp_path: Path):
    __build_bundle(tmp_path)
    api: HfApi = Mock(spec=HfApi)
    api.list_repo_tree.side_effect = [
        [__repo_file("history/2026-01-01/raw.zip"), __repo_file("history/2026-01-01/addons.parquet")],
        [__repo_file("latest/addons.parquet")],
    ]
    client: HuggingFaceClient = HuggingFaceClient(api)

    client.prune_orphans(tmp_path)

    api.delete_files.assert_not_called()
