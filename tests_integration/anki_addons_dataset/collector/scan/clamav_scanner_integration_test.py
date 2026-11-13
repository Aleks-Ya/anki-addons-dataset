import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from anki_addons_dataset.collector.scan.clamav_scanner import ClamavScanner, ClamavVersion

# Split in two so that this source file itself does not match the EICAR test signature.
__EICAR: str = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-" + "STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


def __package(directory: Path, name: str, content: str) -> Path:
    package_file: Path = directory / name
    with zipfile.ZipFile(package_file, "w") as archive:
        archive.writestr("sub/__init__.py", content)
    return package_file


def test_scan_finds_the_eicar_test_file_inside_a_package(tmp_path: Path):
    infected: Path = __package(tmp_path, "infected package.ankiaddon", __EICAR)
    clean: Path = __package(tmp_path, "clean.ankiaddon", "a = 1\n")

    signatures: dict[Path, list[str]] = ClamavScanner().scan([infected, clean])

    assert signatures[clean] == []
    assert len(signatures[infected]) == 1
    assert "Eicar" in signatures[infected][0]


def test_verify_access_reports_a_recent_database():
    version: ClamavVersion = ClamavScanner().verify_access()

    assert version.database_version > 0
    assert datetime.now() - version.database_date < timedelta(days=7)
