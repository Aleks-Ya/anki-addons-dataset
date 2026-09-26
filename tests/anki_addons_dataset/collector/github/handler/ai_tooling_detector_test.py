from anki_addons_dataset.collector.github.handler.ai_tooling_detector import AiToolingDetector
from anki_addons_dataset.common.data_types import GithubReadme


def test_no_signals_returns_empty():
    readme: GithubReadme = GithubReadme("# My addon\nA plain description.")
    assert AiToolingDetector.detect(["src/main.py", "README.md", "LICENSE"], readme) == []


def test_empty_inputs():
    assert AiToolingDetector.detect([], None) == []


def test_config_file_fingerprints():
    files: list[str] = [
        "CLAUDE.md",
        ".cursorrules",
        ".github/copilot-instructions.md",
        ".windsurfrules",
        ".aider.conf.yml",
        ".continue/config.json",
        ".clinerules",
        "GEMINI.md",
        "AGENTS.md",
    ]
    markers: list[str] = AiToolingDetector.detect(files, None)
    assert markers == ["agents-md", "aider", "claude-code", "cline", "continue", "copilot", "cursor", "gemini",
                       "windsurf"]


def test_config_dir_fingerprints():
    files: list[str] = [".cursor/rules/style.md", ".claude/settings.json", ".roo/rules.md", ".windsurf/config"]
    markers: list[str] = AiToolingDetector.detect(files, None)
    assert markers == ["claude-code", "cline", "cursor", "windsurf"]


def test_aider_prefix_files():
    assert AiToolingDetector.detect([".aiderignore"], None) == ["aider"]
    assert AiToolingDetector.detect([".aider.chat.history.md"], None) == ["aider"]


def test_readme_provenance_markers():
    readme: GithubReadme = GithubReadme(
        "# Addon\n\n"
        "🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\n"
        "Co-Authored-By: Claude <noreply@anthropic.com>\n"
        "This project was vibe-coded over a weekend."
    )
    assert AiToolingDetector.detect([], readme) == ["claude-code", "vibe-coded"]


def test_readme_made_with():
    assert AiToolingDetector.detect([], GithubReadme("Made with Cursor")) == ["cursor"]
    assert AiToolingDetector.detect([], GithubReadme("made with bolt.new")) == ["bolt"]
    assert AiToolingDetector.detect([], GithubReadme("Made with Lovable")) == ["lovable"]


def test_dedup_across_file_and_readme():
    # A CLAUDE.md file and a Claude README marker collapse to a single slug.
    markers: list[str] = AiToolingDetector.detect(["CLAUDE.md"], GithubReadme("Co-Authored-By: Claude"))
    assert markers == ["claude-code"]
