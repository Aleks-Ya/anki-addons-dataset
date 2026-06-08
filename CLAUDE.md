# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Collects, processes, and publishes structured data about Anki flashcard addons to HuggingFace. It scrapes addon info from AnkiWeb, enriches it with GitHub and Anki Forum data, and exports in JSON, Parquet, and Excel formats.

- HuggingFace dataset: https://huggingface.co/datasets/Ya-Alex/anki-addons
- HuggingFace Spaces: https://huggingface.co/spaces/Ya-Alex/anki-addons

## Commands

```bash
# Run all tests (with coverage)
pytest

# Run a single test file
pytest tests/anki_addons_dataset/path/to/test_file.py

# Run with verbose output
pytest -v

# CLI operations (INIT → DOWNLOAD → PARSE → BUNDLE → UPLOAD)
PYTHONPATH=src python -m anki_addons_dataset.addon_catalog init
PYTHONPATH=src python -m anki_addons_dataset.addon_catalog download -d 2026-01-01
PYTHONPATH=src python -m anki_addons_dataset.addon_catalog parse
PYTHONPATH=src python -m anki_addons_dataset.addon_catalog parse -l INFO  # change log level
PYTHONPATH=src python -m anki_addons_dataset.addon_catalog bundle
PYTHONPATH=src python -m anki_addons_dataset.addon_catalog upload

# Install/update dependencies
./pip_update.sh

# Version bumping
bump-my-version bump release --tag   # SNAPSHOT → release
bump-my-version bump minor            # release → next SNAPSHOT
git push origin HEAD --tags
```

## Architecture

### Pipeline Flow

Five sequential CLI operations form the pipeline:

1. **INIT** — creates `~/anki-addons-dataset/` working directory with `history/` and `bundle/` subdirs
2. **DOWNLOAD** — scrapes AnkiWeb for a given date (`-d YYYY-MM-DD`), saves raw HTML/JSON to `history/YYYY-MM-DD/1-raw/`
3. **PARSE** — reads all snapshots, enriches with GitHub + Anki Forum data, exports to `3-final/` (JSON/Parquet/Excel); re-running PARSE is safe and uses cached raw data
4. **BUNDLE** — zips snapshots, copies finals to `bundle/`, generates HuggingFace dataset card
5. **UPLOAD** — pushes `bundle/` to HuggingFace Hub

### Key Source Areas

- `src/anki_addons_dataset/common/data_types.py` — all core dataclasses (`AddonInfo`, `GithubInfo`, `AnkiForumInfo`, `Aggregation`, etc.) and `NewType` aliases (`AddonId`, `URL`, `SnapshotDate`)
- `src/anki_addons_dataset/collector/` — data collection; `AddonInfosCollector` orchestrates AnkiWeb scraping followed by async GitHub and AnkiForumEnrichers running in background threads
- `src/anki_addons_dataset/exporter/` — multi-format export; `ExporterFacade` delegates to json/parquet/xlsx subpackages
- `src/anki_addons_dataset/facade/` — top-level orchestration wiring operations together
- `src/anki_addons_dataset/common/working_dir.py` — all filesystem path logic lives here

### Design Patterns

- **Facade classes** (`CollectorFacade`, `ExporterFacade`, `Facade`) orchestrate complex multi-step workflows
- **Enrichers** (`GithubEnricher`, `AnkiForumEnricher`) run asynchronously in background threads during PARSE
- **Manual overrides** — `history/YYYY-MM-DD/2-stage/4-overrider/overrides.yaml` lets you fix parsing errors without re-downloading
- Frozen dataclasses used for immutability (e.g., `GithubRepo`)

### Testing

Tests mirror `src/` structure under `tests/`. HTML fixtures for AnkiWeb parser tests are in `src/collector/ankiweb/`. Tests use `conftest.py` with `tmp_path`-based working directories and mocked external APIs. `freezegun` is used for time-sensitive tests.
