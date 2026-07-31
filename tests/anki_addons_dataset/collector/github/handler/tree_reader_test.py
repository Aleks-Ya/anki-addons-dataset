from anki_addons_dataset.collector.github.handler.tree_reader import TreeReader


def test_extract_file_paths():
    content: dict = {"tree": [{"path": "src/app.py"}, {"path": "README.md"}], "truncated": False}
    assert TreeReader.extract_file_paths(content) == ["src/app.py", "README.md"]


def test_extract_file_paths_truncated_returns_empty():
    content: dict = {"tree": [{"path": "src/app.py"}], "truncated": True}
    assert TreeReader.extract_file_paths(content) == []


def test_extract_file_paths_missing_tree_returns_empty():
    assert TreeReader.extract_file_paths({}) == []


def test_extract_file_paths_skips_entries_without_path():
    content: dict = {"tree": [{"path": "a.py"}, {"sha": "abc"}], "truncated": False}
    assert TreeReader.extract_file_paths(content) == ["a.py"]
