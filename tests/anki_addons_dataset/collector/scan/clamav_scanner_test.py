import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from anki_addons_dataset.collector.scan.clamav_scanner import ClamavError, ClamavScanner, ClamavVersion

__RUN: str = "anki_addons_dataset.collector.scan.clamav_scanner.subprocess.run"


def __completed(stdout: str, returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


def __package(tmp_path: Path, name: str) -> Path:
    package_file: Path = tmp_path / name
    package_file.write_bytes(b"zip")
    return package_file


def test_version_parses_the_daemon_version():
    with patch(__RUN, return_value=__completed("ClamAV 1.5.4/28181/Thu Nov 12 13:27:14 2026\n")) as run:
        version: ClamavVersion = ClamavScanner().version()

    assert version == ClamavVersion("1.5.4", 28181, datetime(2026, 11, 12, 13, 27, 14))
    assert run.call_args.args[0] == ["clamdscan", "--version"]


def test_version_rejects_an_unexpected_output():
    with patch(__RUN, return_value=__completed("ClamAV 1.5.4\n")):
        with pytest.raises(ClamavError, match="Unexpected 'clamdscan --version' output: ClamAV 1.5.4"):
            ClamavScanner().version()


def test_scan_reports_signatures_and_clean_files(tmp_path: Path):
    infected: Path = __package(tmp_path, "bad file.ankiaddon")
    clean: Path = __package(tmp_path, "clean.ankiaddon")
    stdout: str = f"{infected}: Eicar-Test-Signature FOUND\n{clean}: OK\n"

    with patch(__RUN, return_value=__completed(stdout, 1)) as run:
        signatures: dict[Path, list[str]] = ClamavScanner().scan([infected, clean])

    assert signatures == {infected: ["Eicar-Test-Signature"], clean: []}
    assert run.call_args.args[0] == ["clamdscan", "--fdpass", "--no-summary", "--stdout", str(infected), str(clean)]


def test_scan_keeps_every_signature_of_a_file(tmp_path: Path):
    infected: Path = __package(tmp_path, "a.ankiaddon")
    stdout: str = f"{infected}: Win.Trojan.Agent-1 FOUND\n{infected}: Eicar-Test-Signature FOUND\n"

    with patch(__RUN, return_value=__completed(stdout, 1)):
        signatures: dict[Path, list[str]] = ClamavScanner().scan([infected])

    assert signatures == {infected: ["Win.Trojan.Agent-1", "Eicar-Test-Signature"]}


def test_scan_fails_on_a_file_without_result(tmp_path: Path):
    infected: Path = __package(tmp_path, "a.ankiaddon")
    missing: Path = tmp_path / "missing.ankiaddon"
    stdout: str = f"{infected}: Eicar-Test-Signature FOUND\nERROR: Can't access file {missing}\n"

    with patch(__RUN, return_value=__completed(stdout, 1)):
        with pytest.raises(ClamavError, match="gave no result for"):
            ClamavScanner().scan([infected, missing])


def test_scan_fails_on_exit_code_2(tmp_path: Path):
    package_file: Path = __package(tmp_path, "a.ankiaddon")

    with patch(__RUN, return_value=__completed("", 2, "Could not connect to clamd")):
        with pytest.raises(ClamavError, match="exit code 2.*Could not connect to clamd"):
            ClamavScanner().scan([package_file])


def test_scan_explains_a_missing_clamdscan(tmp_path: Path):
    package_file: Path = __package(tmp_path, "a.ankiaddon")

    with patch(__RUN, side_effect=FileNotFoundError("clamdscan")):
        with pytest.raises(ClamavError, match="install ClamAV"):
            ClamavScanner().scan([package_file])


def test_verify_access_scans_a_clean_probe():
    def run(arguments: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        if arguments[1] == "--version":
            return __completed("ClamAV 1.5.4/28181/Thu Nov 12 13:27:14 2026\n")
        return __completed(f"{arguments[-1]}: OK\n")

    with patch(__RUN, side_effect=run):
        version: ClamavVersion = ClamavScanner().verify_access()

    assert version.database_version == 28181


def test_verify_access_fails_when_the_probe_is_infected():
    run: Mock = Mock(side_effect=lambda arguments, **_: __completed(f"{arguments[-1]}: Some.Signature FOUND\n", 1))

    with patch(__RUN, run):
        with pytest.raises(ClamavError, match="clean probe file as infected"):
            ClamavScanner().verify_access()
