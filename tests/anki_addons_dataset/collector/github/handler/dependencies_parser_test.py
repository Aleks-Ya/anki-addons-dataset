from anki_addons_dataset.collector.github.handler.dependencies_parser import DependenciesParser
from anki_addons_dataset.common.data_types import DependencyName


def test_parse_requirements_names_only():
    content: str = "requests>=2.0\nbeautifulsoup4==4.12.0\npydantic~=2.5\nrich\n"
    assert DependenciesParser.parse_requirements(content) == [
        DependencyName("requests"), DependencyName("beautifulsoup4"), DependencyName("pydantic"),
        DependencyName("rich")]


def test_parse_requirements_skips_comments_options_and_blanks():
    content: str = "# a comment\n\n-r other.txt\n--hash=sha256:abc\nrequests\n"
    assert DependenciesParser.parse_requirements(content) == [DependencyName("requests")]


def test_parse_requirements_dedupes():
    content: str = "requests\nrequests>=2.0\n"
    assert DependenciesParser.parse_requirements(content) == [DependencyName("requests")]


def test_parse_requirements_none_or_empty():
    assert DependenciesParser.parse_requirements(None) == []
    assert DependenciesParser.parse_requirements("") == []


def test_parse_pyproject_pep621():
    content: str = """
[project]
name = "addon"
dependencies = ["requests>=2.0", "rich"]
"""
    assert DependenciesParser.parse_pyproject(content) == [DependencyName("requests"), DependencyName("rich")]


def test_parse_pyproject_poetry_excludes_python():
    content: str = """
[tool.poetry.dependencies]
python = "^3.11"
requests = "^2.0"
rich = "*"
"""
    assert DependenciesParser.parse_pyproject(content) == [DependencyName("requests"), DependencyName("rich")]


def test_parse_pyproject_malformed_returns_empty():
    assert DependenciesParser.parse_pyproject("not = = toml") == []


def test_parse_pyproject_none():
    assert DependenciesParser.parse_pyproject(None) == []
