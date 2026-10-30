from pathlib import Path
from unittest.mock import patch

from anki_addons_dataset.common.file_links import FileLinks


def test_hardlinks_when_possible(tmp_path: Path):
    source: Path = tmp_path / "source"
    source.write_text("content")
    target: Path = tmp_path / "sub" / "target"

    FileLinks.link_or_copy(source, target)

    assert target.stat().st_ino == source.stat().st_ino


def test_copies_when_hardlink_fails(tmp_path: Path):
    source: Path = tmp_path / "source"
    source.write_text("content")
    target: Path = tmp_path / "target"

    with patch("os.link", side_effect=OSError("cross-device")):
        FileLinks.link_or_copy(source, target)

    assert target.read_text() == "content"
    assert target.stat().st_ino != source.stat().st_ino
    assert not (tmp_path / "target.part").exists()


def test_follows_symlinks(tmp_path: Path):
    blob: Path = tmp_path / "blob"
    blob.write_text("content")
    symlink: Path = tmp_path / "symlink"
    symlink.symlink_to(blob)
    target: Path = tmp_path / "target"

    FileLinks.link_or_copy(symlink, target)

    assert not target.is_symlink()
    assert target.stat().st_ino == blob.stat().st_ino


def test_keeps_existing_target(tmp_path: Path):
    source: Path = tmp_path / "source"
    source.write_text("new")
    target: Path = tmp_path / "target"
    target.write_text("old")

    FileLinks.link_or_copy(source, target)

    assert target.read_text() == "old"
