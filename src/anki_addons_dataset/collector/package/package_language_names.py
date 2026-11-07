from typing import Optional

from anki_addons_dataset.common.data_types import LanguageName


class PackageLanguageNames:
    __names: dict[str, str] = {
        "asm": "Assembly", "asp": "Classic ASP", "autohotkey": "AutoHotkey", "autoit": "AutoIt", "awk": "Awk",
        "batch": "Batchfile", "bazel": "Starlark", "c": "C", "clojure": "Clojure", "cmake": "CMake", "cobol": "COBOL",
        "coffeescript": "CoffeeScript", "cpp": "C++", "cs": "C#", "csproj": "XML", "css": "CSS", "csv": "CSV",
        "dart": "Dart", "dm": "DM", "dockerfile": "Dockerfile", "elixir": "Elixir", "erb": "HTML+ERB",
        "erlang": "Erlang", "gemfile": "Ruby", "gemspec": "Ruby", "gitattributes": "Git Attributes",
        "gitmodules": "Git Config", "go": "Go", "gradle": "Gradle", "groovy": "Groovy", "handlebars": "Handlebars",
        "haskell": "Haskell", "hcl": "HCL", "htaccess": "ApacheConf", "html": "HTML", "ignorefile": "Ignore List",
        "ipynb": "Jupyter Notebook", "java": "Java", "javascript": "JavaScript", "jinja": "Jinja", "json": "JSON",
        "jsonl": "JSON", "julia": "Julia", "kotlin": "Kotlin", "lisp": "Common Lisp", "lua": "Lua", "m4": "M4",
        "makefile": "Makefile", "matlab": "MATLAB", "mht": "MHTML", "objectivec": "Objective-C", "ocaml": "OCaml",
        "pascal": "Pascal", "perl": "Perl", "php": "PHP", "powershell": "PowerShell", "prolog": "Prolog",
        "proto": "Protocol Buffer", "python": "Python", "r": "R", "ruby": "Ruby", "rust": "Rust", "scala": "Scala",
        "scss": "SCSS", "shell": "Shell", "smali": "Smali", "solidity": "Solidity", "sql": "SQL", "swift": "Swift",
        "tcl": "Tcl", "textproto": "Protocol Buffer Text Format", "tsv": "TSV", "twig": "Twig",
        "typescript": "TypeScript", "vba": "VBA", "vcxproj": "XML", "verilog": "Verilog", "vhdl": "VHDL", "vue": "Vue",
        "xml": "XML", "yaml": "YAML", "yara": "YARA", "zig": "Zig"}

    @staticmethod
    def linguist_name(label: str) -> LanguageName:
        name: Optional[str] = PackageLanguageNames.__names.get(label)
        if name is None:
            raise ValueError(f"No language name for the Magika label '{label}'")
        return LanguageName(name)
