from pathlib import Path
from zipfile import BadZipFile, ZipFile

import pytest

from anki_addons_dataset.collector.package.package_analyzer import PackageAnalysis, PackageAnalyzer


def __package(tmp_path: Path, entries: dict[str, bytes]) -> Path:
    package_file: Path = tmp_path / "package.ankiaddon"
    with ZipFile(package_file, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return package_file


def test_analyze_counts_files_and_python_lines(tmp_path: Path):
    package_file: Path = __package(tmp_path, {
        "__init__.py": b"import aqt\nprint(1)",
        "sub/module.py": b"a = 1\r\nb = 2\r\nc = 3\r\n",
        "web/style.css": b"body {}",
    })

    analysis: PackageAnalysis = PackageAnalyzer().analyze(package_file)

    assert analysis == PackageAnalysis(None, None, 3, 47, 2, 5, ["__init__.py", "sub/module.py", "web/style.css"])


def test_analyze_reads_manifest_and_config_at_the_root(tmp_path: Path):
    package_file: Path = __package(tmp_path, {
        "manifest.json": b'\xef\xbb\xbf{"name": "Addon"}',
        "config.json": '{"café": 1}'.encode(),
        "sub/manifest.json": b"{}",
    })

    analysis: PackageAnalysis = PackageAnalyzer().analyze(package_file)

    assert analysis.manifest_json == '{"name": "Addon"}'
    assert analysis.config_json == '{"café": 1}'


def test_analyze_keeps_metadata_that_is_not_valid_text(tmp_path: Path):
    package_file: Path = __package(tmp_path, {"config.json": b'{"a": "\xff"}'})

    assert PackageAnalyzer().analyze(package_file).config_json == '{"a": "�"}'


def test_analyze_excludes_macos_junk(tmp_path: Path):
    package_file: Path = __package(tmp_path, {
        "__init__.py": b"a = 1\n",
        "__MACOSX/.___init__.py": b"\x00\x05junk\n",
        "__MACOSX/manifest.json": b"{}",
        "sub/._module.py": b"\x00\x05junk\n",
    })

    analysis: PackageAnalysis = PackageAnalyzer().analyze(package_file)

    assert analysis == PackageAnalysis(None, None, 1, 6, 1, 1, ["__init__.py"])


def test_analyze_skips_directory_entries(tmp_path: Path):
    package_file: Path = __package(tmp_path, {"sub/": b"", "sub/module.py": b"a = 1\n"})

    assert PackageAnalyzer().analyze(package_file).files == ["sub/module.py"]


def test_analyze_ignores_metadata_over_the_limit(tmp_path: Path):
    package_file: Path = __package(tmp_path, {"config.json": b"x" * 64_001, "manifest.json": b"x" * 64_000})

    analysis: PackageAnalysis = PackageAnalyzer().analyze(package_file)

    assert analysis.config_json is None
    assert analysis.manifest_json == "x" * 64_000


def test_analyze_counts_a_python_file_over_the_limit_without_reading_it(tmp_path: Path):
    package_file: Path = __package(tmp_path, {"big.py": b"\n" * 5_000_001, "small.py": b"a = 1\n"})

    analysis: PackageAnalysis = PackageAnalyzer().analyze(package_file)

    assert analysis.python_file_count == 2
    assert analysis.python_lines == 1
    assert analysis.uncompressed_bytes == 5_000_007


def test_analyze_raises_on_a_corrupt_package(tmp_path: Path):
    package_file: Path = tmp_path / "package.ankiaddon"
    package_file.write_bytes(b"not a zip")
    analyzer: PackageAnalyzer = PackageAnalyzer()

    with pytest.raises(BadZipFile):
        analyzer.analyze(package_file)
