import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class ClamavError(Exception):
    pass


@dataclass(frozen=True)
class ClamavVersion:
    engine: str
    database_version: int
    database_date: datetime


class ClamavScanner:
    __command: str = "clamdscan"
    __found_suffix: str = " FOUND"
    __ok_suffix: str = ": OK"

    def version(self) -> ClamavVersion:
        output: str = self.__run(["--version"]).stdout.strip()
        try:
            engine, database_version, database_date = output.removeprefix("ClamAV ").split("/", 2)
            return ClamavVersion(engine, int(database_version),
                                 datetime.strptime(database_date, "%a %b %d %H:%M:%S %Y"))
        except ValueError as e:
            raise ClamavError(f"Unexpected '{ClamavScanner.__command} --version' output: {output}") from e

    def scan(self, files: list[Path]) -> dict[Path, list[str]]:
        resolved: dict[str, Path] = {str(file.resolve()): file for file in files}
        completed: subprocess.CompletedProcess[str] = self.__run(
            ["--fdpass", "--no-summary", "--stdout", *resolved])
        if completed.returncode not in (0, 1):
            raise ClamavError(f"{ClamavScanner.__command} failed with exit code {completed.returncode}: "
                              f"{completed.stdout.strip()} {completed.stderr.strip()}")
        signatures: dict[Path, list[str]] = {}
        for line in completed.stdout.splitlines():
            if line.endswith(ClamavScanner.__found_suffix):
                path, signature = line.removesuffix(ClamavScanner.__found_suffix).rsplit(": ", 1)
                if path in resolved:
                    signatures.setdefault(resolved[path], []).append(signature)
            elif line.endswith(ClamavScanner.__ok_suffix):
                path = line.removesuffix(ClamavScanner.__ok_suffix)
                if path in resolved:
                    signatures.setdefault(resolved[path], [])
        missing: list[str] = [path for path, file in resolved.items() if file not in signatures]
        if missing:
            raise ClamavError(f"{ClamavScanner.__command} gave no result for {missing}: "
                              f"{completed.stdout.strip()} {completed.stderr.strip()}")
        return signatures

    def verify_access(self) -> ClamavVersion:
        with tempfile.TemporaryDirectory() as temp_dir:
            probe: Path = Path(temp_dir) / "probe.ankiaddon"
            with zipfile.ZipFile(probe, "w") as archive:
                archive.writestr("__init__.py", "a = 1\n")
            if self.scan([probe]) != {probe: []}:
                raise ClamavError(f"ClamAV reports a clean probe file as infected: {probe}")
        return self.version()

    @staticmethod
    def __run(arguments: list[str]) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run([ClamavScanner.__command, *arguments], capture_output=True, text=True,
                                  check=False)
        except FileNotFoundError as e:
            raise ClamavError(f"'{ClamavScanner.__command}' not found: install ClamAV and start its clamd "
                              f"daemon") from e
