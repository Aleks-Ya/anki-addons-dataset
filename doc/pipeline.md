# Running the pipeline

## Snapshot date (`-d`)

`ai`, `parse` and `report` process every snapshot in `history/` by default. With `-d` they process
that one snapshot only:

```bash
anki-addons-dataset ai -d 2026-01-01
anki-addons-dataset parse -d 2026-01-01
anki-addons-dataset report -d 2026-01-01
anki-addons-dataset parse report -d 2026-01-01   # re-parse and re-report one snapshot
```

The date must name a snapshot that was already downloaded, otherwise the step fails. It also wins over
`--sample-snapshots`. `bundle` ignores `-d` and always bundles the whole history.

Inside `all`, `-d` is the date `download` scrapes. The `ai`, `parse` and `report` steps of `all` still
process every snapshot. They take the date only when they are named explicitly, as in
`download parse report -d 2026-01-01`.

There are three ways to run it, depending on which version you need, plus a sampled run for
testing a change quickly:

## 1. Full run on a release version (from PyPI)

Latest release (default):
```bash
uvx anki-addons-dataset all -d 2026-01-01
```

A specific release:
```bash
uvx --from anki-addons-dataset==1.3.0 anki-addons-dataset all -d 2026-01-01
```

`uvx` runs the released package in an isolated, cached environment — it never touches the
editable dev install. If a brand-new release is not picked up, add `--refresh` once.

## 2. Given steps on a release version (from PyPI)

```bash
uvx anki-addons-dataset parse report                                   # latest release
uvx --from anki-addons-dataset==1.3.0 anki-addons-dataset parse report  # pinned release
```

## 3. Given steps on the current working source

`uv sync` installs the project in editable mode, so `uv run` executes your working tree:
```bash
uv run anki-addons-dataset parse report
```

Or run the source explicitly without relying on the install:
```bash
PYTHONPATH=src python -m anki_addons_dataset.addon_catalog parse report
```

## 4. Sample run: a slice of the dataset
Testing a change end-to-end against the real working directory means thousands of addon pages per
snapshot and the whole history re-parsed. Two limits cut that down to a slice of it, and combine
freely; point `-w` at a scratch directory so the real one is never touched:

| Option | Meaning |
| --- | --- |
| `--sample-addons` | download and parse only the first N addons, ordered by addon id |
| `--sample-snapshots` | let `ai`/`parse`/`report` (without `-d`) and `bundle` process only the newest N snapshots |

```bash
WD=/tmp/anki-addons-sample
uv run anki-addons-dataset init -w $WD
uv run anki-addons-dataset download -d $(date +%F) -w $WD --sample-addons 20
uv run anki-addons-dataset parse report bundle -w $WD
```

The `download` is a real scrape, just a short one, so it needs headless Chrome and the GitHub token.
It records the addon limit in `1-raw/sample.json`, which is why the second command needs no flag: an
offline `parse` of a sampled snapshot would otherwise ask for an addon page that was never
downloaded. Add `ai` only when the AI path is what is being tested — it bills per addon.

`--sample-snapshots` is the axis that matters once the scratch directory holds several dates.

A sampled run never uploads: `upload` on its own is rejected, and `all` runs through `bundle` and
skips it, so a partial dataset cannot reach HuggingFace.
