from pathlib import Path
from zipfile import BadZipFile, ZipFile

import pytest

from anki_addons_dataset.collector.package.package_analyzer import PackageAnalysis, PackageAnalyzer
from anki_addons_dataset.common.data_types import LanguageName

__PYTHON: bytes = (b'import os\nimport sys\n\n\ndef main():\n    for path in sys.argv[1:]:\n'
                   b'        print(os.path.getsize(path))\n\n\nif __name__ == "__main__":\n    main()\n')
__JAVASCRIPT: bytes = (b'function add(a, b) {\n    return a + b;\n}\n\n'
                       b'document.addEventListener("DOMContentLoaded", () => {\n    console.log(add(1, 2));\n});\n')
__CSS: bytes = (b'body {\n    margin: 0;\n    font-family: sans-serif;\n}\n\n'
                b'.card {\n    color: #333;\n    padding: 4px 8px;\n}\n')
__MARKDOWN: bytes = (b'# My addon\n\nThis addon adds a button to the reviewer.\n\n## Usage\n\n'
                     b'Press the button and enjoy your reviews.\n')


@pytest.fixture
def analyzer() -> PackageAnalyzer:
    return PackageAnalyzer()


def __package(tmp_path: Path, entries: dict[str, bytes]) -> Path:
    package_file: Path = tmp_path / "package.ankiaddon"
    package_file.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(package_file, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return package_file


def test_analyze_counts_files_and_python_lines(analyzer: PackageAnalyzer, tmp_path: Path):
    package_file: Path = __package(tmp_path, {
        "__init__.py": b"import aqt\nprint(1)",
        "sub/module.py": b"a = 1\r\nb = 2\r\nc = 3\r\n",
        "web/style.css": b"body {}",
    })

    analysis: PackageAnalysis = analyzer.analyze(package_file)

    assert analysis == PackageAnalysis(None, None, 3, 47, 2, 5, ["__init__.py", "sub/module.py", "web/style.css"],
                                       {LanguageName("python"): 19})


def test_analyze_reads_manifest_and_config_at_the_root(analyzer: PackageAnalyzer, tmp_path: Path):
    package_file: Path = __package(tmp_path, {
        "manifest.json": b'\xef\xbb\xbf{"name": "Addon"}',
        "config.json": '{"café": 1}'.encode(),
        "sub/manifest.json": b"{}",
    })

    analysis: PackageAnalysis = analyzer.analyze(package_file)

    assert analysis.manifest_json == '{"name": "Addon"}'
    assert analysis.config_json == '{"café": 1}'


def test_analyze_keeps_metadata_that_is_not_valid_text(analyzer: PackageAnalyzer, tmp_path: Path):
    package_file: Path = __package(tmp_path, {"config.json": b'{"a": "\xff"}'})

    assert analyzer.analyze(package_file).config_json == '{"a": "�"}'


def test_analyze_excludes_macos_junk(analyzer: PackageAnalyzer, tmp_path: Path):
    package_file: Path = __package(tmp_path, {
        "__init__.py": b"a = 1\n",
        "__MACOSX/.___init__.py": b"\x00\x05junk\n",
        "__MACOSX/manifest.json": b"{}",
        "sub/._module.py": b"\x00\x05junk\n",
    })

    analysis: PackageAnalysis = analyzer.analyze(package_file)

    assert analysis == PackageAnalysis(None, None, 1, 6, 1, 1, ["__init__.py"], {})


def test_analyze_skips_directory_entries(analyzer: PackageAnalyzer, tmp_path: Path):
    package_file: Path = __package(tmp_path, {"sub/": b"", "sub/module.py": b"a = 1\n"})

    assert analyzer.analyze(package_file).files == ["sub/module.py"]


def test_analyze_ignores_metadata_over_the_limit(analyzer: PackageAnalyzer, tmp_path: Path):
    package_file: Path = __package(tmp_path, {"config.json": b"x" * 64_001, "manifest.json": b"x" * 64_000})

    analysis: PackageAnalysis = analyzer.analyze(package_file)

    assert analysis.config_json is None
    assert analysis.manifest_json == "x" * 64_000


def test_analyze_counts_a_python_file_over_the_limit_without_reading_it(analyzer: PackageAnalyzer, tmp_path: Path):
    package_file: Path = __package(tmp_path, {"big.py": b"\n" * 5_000_001, "small.py": b"a = 1\n"})

    analysis: PackageAnalysis = analyzer.analyze(package_file)

    assert analysis.python_file_count == 2
    assert analysis.python_lines == 1
    assert analysis.uncompressed_bytes == 5_000_007


def test_analyze_raises_on_a_corrupt_package(analyzer: PackageAnalyzer, tmp_path: Path):
    package_file: Path = tmp_path / "package.ankiaddon"
    package_file.write_bytes(b"not a zip")

    with pytest.raises(BadZipFile):
        analyzer.analyze(package_file)


def test_analyze_detects_languages_by_content(analyzer: PackageAnalyzer, tmp_path: Path):
    package_file: Path = __package(tmp_path, {
        "__init__.py": __PYTHON,
        "web/script.txt": __JAVASCRIPT,
        "web/style.css": __CSS,
        "web/more.css": __CSS,
    })

    analysis: PackageAnalysis = analyzer.analyze(package_file)

    assert analysis.language_bytes == {LanguageName("css"): 206, LanguageName("python"): 142,
                                       LanguageName("javascript"): 128}


def test_analyze_does_not_count_files_outside_the_code_group(analyzer: PackageAnalyzer, tmp_path: Path):
    package_file: Path = __package(tmp_path, {
        "README.md": __MARKDOWN,
        "icon.png": b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 4,
        "empty.py": b"",
        "tiny.py": b"a = 1\n",
    })

    assert analyzer.analyze(package_file).language_bytes == {}


def test_analyze_does_not_detect_languages_of_macos_junk(analyzer: PackageAnalyzer, tmp_path: Path):
    package_file: Path = __package(tmp_path, {"__MACOSX/.___init__.py": __PYTHON, "sub/._module.py": __PYTHON})

    assert analyzer.analyze(package_file).language_bytes == {}


def test_analyze_does_not_detect_the_language_of_a_file_over_the_limit(analyzer: PackageAnalyzer, tmp_path: Path):
    package_file: Path = __package(tmp_path, {"big.py": __PYTHON * 40_000, "small.py": __PYTHON})

    assert analyzer.analyze(package_file).language_bytes == {LanguageName("python"): 142}


def test_analyze_reuses_the_analysis_of_a_package_with_the_same_name(analyzer: PackageAnalyzer, tmp_path: Path):
    first_file: Path = __package(tmp_path / "first", {"__init__.py": __PYTHON})
    second_file: Path = __package(tmp_path / "second", {"__init__.py": __PYTHON})
    second_file.write_bytes(b"not a zip")

    first_analysis: PackageAnalysis = analyzer.analyze(first_file)

    assert analyzer.analyze(second_file) == first_analysis
