# Integration tests
Live tests against AnkiWeb, GitHub, the Anki Forum and HuggingFace. They exist to catch upstream
breakage that no code change causes — changed AnkiWeb markup, a changed GitHub API response shape, a
changed Discourse timestamp format, changed HuggingFace auth behaviour.

Run locally: `uv run pytest tests_integration`, or use the `Integration tests` PyCharm run
configuration (`.run/Integration tests.run.xml`). Individual files and tests run from the IDE gutter
as usual.

They are **never executed in GitHub Actions**: `pytest.ini` sets `testpaths = tests`, so the bare
`uv run pytest` that CI runs does not collect `tests_integration/`.

Requirements:
- headless Chrome (resolved by Selenium Manager) for the AnkiWeb tests
- a GitHub personal access token in `~/.github/token.txt` (see `github.token_file` in the config)
- an AI API key in the file `ai.api_key_file` points at (the AI tests bill your account)
- a write-capable HuggingFace token via `HF_TOKEN` or `hf auth login`

Missing credentials make the tests **fail**, not skip — the point is to tell you the local setup is
broken. All tests are read-only (nothing is uploaded, tagged or deleted on HuggingFace) and write
only into a `tmp_path`, so `~/anki-addons-dataset/` is never touched.
