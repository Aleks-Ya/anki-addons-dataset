---
paths:
  - "**/*.py"
---

# Python Code Style Guidelines

## Comments

- Add comments and docstrings only when unavoidable — when the code cannot be made self-explanatory through naming
  and structure, or when a non-obvious decision needs its rationale recorded. Do not restate what the
  code already says.

## Data types

- Use frozen dataclasses for immutability (e.g. `GithubRepo`).

## Tests

- A new test mirrors the `src/` structure under `tests/`.
- HTML fixtures for the AnkiWeb parser tests live in `src/collector/ankiweb/`.
- Use `conftest.py` with `tmp_path`-based working directories and mock every external API: the whole
  suite must run without network access.
- Use `freezegun` for time-sensitive tests.
- A live test against a real service belongs in `tests_integration/`, in the same mirrored layout,
  named `*_integration_test.py`, and uses that tree's own `conftest.py` with *real* clients.
- An integration test stays read-only, writes only under `tmp_path`, and fails rather than skips when
  credentials are missing.
