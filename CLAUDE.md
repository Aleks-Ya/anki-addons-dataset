# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Collects, processes, and publishes structured data about Anki flashcard addons to HuggingFace. It scrapes addon info from AnkiWeb, enriches it with GitHub and Anki Forum data, and exports in JSON, Parquet, and Excel formats.

- HuggingFace dataset: https://huggingface.co/datasets/Ya-Alex/anki-addons
- HuggingFace Spaces: https://huggingface.co/spaces/Ya-Alex/anki-addons

## Commands

```bash
# Run all tests (coverage is opt-in; pytest.ini sets no addopts)
uv run pytest

# Run a single test file
uv run pytest tests/anki_addons_dataset/path/to/test_file.py

# Run with verbose output and coverage (as CI does)
uv run pytest -v --cov=anki_addons_dataset --cov-report=xml --cov-branch

# CLI operations (INIT → DOWNLOAD → AI → PARSE → REPORT → BUNDLE → UPLOAD)
# A single invocation accepts any subset of steps; `all` expands to `info` + the full seven-step sequence.
# `info` is a side-effect-free step that logs the app version and runtime configuration,
# then fails fast on bad credentials: it validates the GitHub token (~/.github/token.txt)
# against the API and checks HuggingFace write access. Both are network calls.
uv run anki-addons-dataset all -d 2026-01-01  # full pipeline (info first)
uv run anki-addons-dataset info               # print version + config only
uv run anki-addons-dataset init
uv run anki-addons-dataset download -d 2026-01-01
uv run anki-addons-dataset ai                 # generate AI summaries for every snapshot (costs money)
uv run anki-addons-dataset parse
uv run anki-addons-dataset parse -l INFO  # change log level (wins over the config file)
# Optional config file: ~/.anki-addons-dataset.yaml (see config.yaml.example), or:
uv run anki-addons-dataset parse -c /path/to/config.yaml
# Working directory override (wins over the config file), e.g. for a scratch run
uv run anki-addons-dataset init -w ~/anki-addons-scratch
# Sample run: a slice of the dataset for testing changes (see the sampling notes below)
uv run anki-addons-dataset download -d 2026-01-01 -w ~/anki-addons-scratch --sample-addons 20
uv run anki-addons-dataset parse report bundle -w ~/anki-addons-scratch --sample-snapshots 2
# Selenium timeouts for DOWNLOAD, in seconds (both default to 120)
uv run anki-addons-dataset download -d 2026-01-01 --page-load-timeout 180 --element-wait-timeout 30
uv run anki-addons-dataset report
uv run anki-addons-dataset bundle
uv run anki-addons-dataset upload

# Create/refresh the venv from the committed lock file
uv sync

# Upgrade all dependencies (refreshes uv.lock)
./uv_update.sh

# Version bumping
uv run bump-my-version bump release --tag   # dev → release (1.3.0.dev0 → 1.3.0)
uv run bump-my-version bump minor            # release → next dev (1.3.0 → 1.4.0.dev0)
git push origin HEAD --tags
```

## Architecture

### Pipeline Flow

Seven sequential CLI operations form the pipeline:

1. **INIT** — creates `~/anki-addons-dataset/` working directory with `history/` and `bundle/` subdirs
2. **DOWNLOAD** — scrapes AnkiWeb for a given date (`-d YYYY-MM-DD`), saves raw HTML/JSON to `history/YYYY-MM-DD/1-raw/` (the durable cache). It also writes parsed `AddonInfo` JSONs to `2-stage/` as a side effect, but those are regenerable and get wiped/rebuilt by the next PARSE (see item 4).
3. **AI** — generates the one-sentence addon summary for *every* snapshot (no `-d`). It rebuilds `AddonInfos` from `1-raw/` exactly as PARSE does, asks the configured OpenAI-compatible provider for a summary per addon, and writes the answers to `1-raw/4-ai/ai-cache.jsonl`. It writes *nothing else*: the filled cache is the whole result, and PARSE reads it back. This is the only step that costs money and the only one that may call an AI API. It is separate from DOWNLOAD because the cache key is a hash of the model plus the whole prompt, so editing the prompt template invalidates every entry — as its own step, refilling costs AI tokens instead of a full Selenium re-scrape (**change the prompt → re-run AI only**). Because the key holds no addon id or date, an unchanged prompt has the same key in every snapshot: the step loads one shared in-memory index (`AiCacheIndex`) from *all* snapshots' caches, so an answer already bought anywhere in the history is reused, and a hit is copied into the current snapshot's cache to keep its `1-raw/` self-contained (`raw.zip` is what `init` restores from). PARSE stays snapshot-local and reads only that snapshot's own cache. AI deliberately does *not* call `SnapshotDir.create()`: it only fills `1-raw/`, and wiping `3-final/` would discard an existing report.
4. **PARSE** — reads all snapshots, rebuilds `AddonInfos` from `1-raw/`, enriches with GitHub + Anki Forum data, and serializes the fully-enriched, overridden `AddonInfos` to `history/YYYY-MM-DD/addon-infos.json` (one faithful dump per snapshot; also writes the `2-stage/` debug trail). PARSE does *not* produce `3-final/` — that is REPORT's job. Re-running PARSE is safe and uses cached raw data; it reprocesses *every* snapshot's cached raw data with the current parsing algorithm, so improving the parsing/enrichment logic regenerates the dumps for the entire history. PARSE rebuilds from `1-raw/` every run rather than reusing the `AddonInfos` DOWNLOAD already builds in memory (DOWNLOAD discards them). This is intentional: `1-raw/` is the single source of truth, and `SnapshotDir.create()` wipes `2-stage/`/`3-final/` on every DOWNLOAD *and* PARSE run. Reusing DOWNLOAD's output would export the newest snapshot with the download-time algorithm while re-parsed history uses the current one — silently inconsistent. The only duplicated work is CPU-parsing the newest snapshot (no redundant network); DOWNLOAD parses anyway because it must discover GitHub/forum targets from the AnkiWeb pages. PARSE also attaches the AI summaries, reading them from `1-raw/4-ai/ai-cache.jsonl` with an offline provider that never calls the network: an addon with no cached answer keeps `ai=None` and PARSE logs the miss count.
5. **REPORT** — reads each snapshot's `addon-infos.json` dump, aggregates, and exports to `3-final/` (JSON/Parquet/Excel) — wiping only `3-final/` (via `SnapshotDir.create_final_dir()`), leaving `2-stage/` and the dump intact. Splitting PARSE (slow, re-parses raw) from REPORT (fast, reads the dump) lets you iterate on export/report logic without re-parsing the whole history: **change parsing/enrichment logic → re-run PARSE; change export/report logic → re-run REPORT only.** REPORT fails with a clear error if a dump is missing (run PARSE first) and warns if the dump's recorded `script_version` differs from the current one (stale dump — re-run PARSE). The `addon-infos.json` dump is a local pipeline cache and is *not* bundled/uploaded (BUNDLE ignores snapshot-root files other than `metadata.json`).
6. **BUNDLE** — zips snapshots, copies finals to `bundle/`, generates HuggingFace dataset card. BUNDLE intentionally re-bundles *all* historical snapshots (not just new ones) so that reports regenerated by an improved REPORT are republished across the full history.
7. **UPLOAD** — syncs `bundle/` to HuggingFace Hub in three non-destructive steps: (0) `tag_backup` tags the current remote head as `backup-YYYY-MM-DD-HHMMSS` (UTC) *before* anything is pushed, pinning the pre-upload commit so it stays reachable and immune to LFS garbage collection — a named point to `git reset`/rollback to if the upload corrupts the dataset; tagging is best-effort and never blocks the upload (Git history alone remains recoverable); (1) `upload_dataset` fails fast if write access is missing, then pushes the bundle with `upload_folder` (suited to the multi-GB, growing dataset); (2) `prune_orphans` then deletes only the remote files under `history/`/`latest/` that no longer exist in the local bundle. Upload runs *before* prune, so the published dataset is never left broken mid-run (the old delete-then-upload approach emptied the dataset first and left it broken if the upload failed). the upload step is kept free of `delete_patterns`, hence the separate prune step

### Sampling

`--sample-addons N` / `--sample-snapshots N` (or the `sample` config section) shrink a run to a slice
of the dataset for testing. Two seams carry them:

- **Addons** — `AddonInfosCollector.collect_addons` slices the header list right after
  `AnkiWebService.get_headers()`, keeping the first N by addon id (the parser already returns them
  sorted, so the slice is stable across DOWNLOAD/AI/PARSE). It must happen *before* any addon is
  enqueued: `GithubEnricher.enrich` expects an entry for every addon it was handed.
- **Snapshots** — `WorkingDir.list_sampled_snapshot_dirs()` returns the newest N and is what AI,
  PARSE, REPORT and BUNDLE iterate. `list_snapshot_dirs()` stays unfiltered on purpose, because
  `get_previous_snapshot_dir` (DOWNLOAD's GitHub 304 reuse) and the shared AI cache index must keep
  seeing the full history.

DOWNLOAD records the addon limit in `1-raw/sample.json` (`SampleCollector`), and the offline steps
re-derive it from there, applying the smaller of the recorded and the configured limit. Without this,
an unsampled PARSE of a sampled snapshot would ask for an addon page that was never downloaded and
fail: `1-raw/1-anki-web/addons_page.html` always lists *every* addon. The limit deliberately lives in
its own file rather than on `RawMetadata`, which is exported into the published reports.

A sampled run must not publish a partial dataset: `_upload_free` in `addon_catalog.py` rejects an
explicit `upload` and drops UPLOAD from `all`, before the first step runs.

### Key Source Areas

- `src/anki_addons_dataset/common/data_types.py` — all core dataclasses (`AddonInfo`, `GithubInfo`, `AnkiForumInfo`, `Aggregation`, etc.) and `NewType` aliases (`AddonId`, `URL`, `SnapshotDate`)
- `src/anki_addons_dataset/collector/` — data collection; `AddonInfosCollector` orchestrates AnkiWeb scraping followed by async GitHub and AnkiForumEnrichers running in background threads
- `src/anki_addons_dataset/collector/ai/` — the AI summary: `AiSummarizer` builds the prompt, `AiProvider`/`OpenAiAiProvider` talk to the endpoint (retrying a transient failure three times, but re-raising a 401/402/403 — a bad key or an empty balance aborts the run instead of failing every addon in turn), `DeepSeekAiProvider` adds the peak-hour refusal and is selected by `CollectorFacade` when `ai.endpoint` is a deepseek.com host, `CachedAiProvider` is the JSONL read-through cache in `1-raw/4-ai/`, `NoAiProvider` stands in where no request may be made, and `AiEnricher` puts the summary on `AddonInfo.ai`
- `src/anki_addons_dataset/exporter/` — multi-format export; `ExporterFacade` delegates to json/parquet/xlsx subpackages
- `src/anki_addons_dataset/facade/` — top-level orchestration wiring operations together
- `src/anki_addons_dataset/common/working_dir.py` — all filesystem path logic lives here
- `src/anki_addons_dataset/config/app_config.py` — `AppConfig` (frozen dataclasses) and `ConfigLoader`, which reads the optional `~/.anki-addons-dataset.yaml` over the built-in defaults. Covers `working_dir`, `github.token_file`, the `ai` block (`endpoint`, `api_key_file`, `model`, `readme_max_chars`), `huggingface.repo_id`/`synced_dirs`, the `sample` block (`addons`, `snapshots`) and the `logging` settings (the log is written to `<working_dir>/logs/anki-addons-dataset.log` by default, always at DEBUG — `logging.level`/`-l` set the console level only, so the logger passes everything and the handlers filter; a relative `logging.file` is resolved against the working directory by `AppConfig.resolved_logging()`, and `logging.file: false` disables file logging). Precedence is CLI flag > config file > default (`-l/--log-level` overrides `logging.level`, `-w/--working-dir` overrides `working_dir`, `--sample-addons`/`--sample-snapshots` override the `sample` block); an unknown key is an error, not a no-op. `addon_catalog.main()` loads it and passes `AppConfig` down through `Facade` → `CollectorFacade`

### Design Patterns

- **Facade classes** (`CollectorFacade`, `ExporterFacade`, `Facade`) orchestrate complex multi-step workflows
- **Enrichers** (`GithubEnricher`, `AnkiForumEnricher`) run asynchronously in background threads during PARSE
- **`AiEnricher` is deliberately not an `Enricher`** — its prompt needs the GitHub README, so it runs over already-enriched `AddonInfos` (after the queue-based enrichers have joined) rather than in parallel with them. The same class serves the AI step (online provider, result discarded, cache is the output) and PARSE (offline provider, result carried into the dump)
- **AddonInfos dump** — PARSE serializes the enriched `AddonInfos` to `history/YYYY-MM-DD/addon-infos.json` via `JsonHelper.write_addon_infos_dump`; REPORT reconstructs them with `JsonHelper.read_addon_infos_dump`. This is the only round-trip (de)serialization of the domain model
- **Manual overrides** — `history/YYYY-MM-DD/2-stage/4-overrider/overrides.yaml` lets you fix parsing errors without re-downloading

### Testing

Live integration tests live in `tests_integration/`. They are outside `pytest.ini`'s `testpaths`, so the bare `uv run pytest` that CI runs never collects them; run them on demand with `uv run pytest tests_integration` or the `Integration tests` PyCharm run config. See README-DEV.md for requirements.
