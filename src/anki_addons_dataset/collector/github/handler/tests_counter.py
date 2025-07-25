import re
from pathlib import Path


class TestsCounter:

    @staticmethod
    def count_tests(files: list[str]) -> int:
        count: int = len([file for file in files if TestsCounter.__is_test(Path(file))])
        return count

    @staticmethod
    def __is_test(file: Path) -> bool:
        return TestsCounter.__is_python_test(file) or \
            TestsCounter.__is_javascript_test(file) or \
            TestsCounter.__is_rust_test(file) or \
            TestsCounter.__is_typescript_test(file) or \
            TestsCounter.__is_c_test(file)

    @staticmethod
    def __is_python_test(file: Path) -> bool:
        return file.name.endswith("_test.py") or re.match(r"test_\w+.py", file.name)

    @staticmethod
    def __is_javascript_test(file: Path) -> bool:
        return file.name.endswith(".test.js") or file.name.endswith(".spec.js") or file.name.endswith(".spec.ts")

    @staticmethod
    def __is_typescript_test(file: Path) -> bool:
        return file.name.endswith(".test.ts") or file.name.endswith(".spec.ts")

    @staticmethod
    def __is_rust_test(file: Path) -> bool:
        return file.name.endswith("_test.rs")

    @staticmethod
    def __is_c_test(file: Path) -> bool:
        return file.name.endswith("_test.c") or re.match(r"test_\w+.c", file.name)
