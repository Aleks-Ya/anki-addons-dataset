# Anki Addons Dataset

A HuggingFace dataset of addons for the [Anki](https://apps.ankiweb.net) flashcard program.

## Install

```bash
pip install anki-addons-dataset
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install anki-addons-dataset   # install the command
uvx anki-addons-dataset info          # or run it once, without installing
```

This installs the `anki-addons-dataset` command. The pipeline runs as a sequence of operations:

```bash
anki-addons-dataset info
anki-addons-dataset init
anki-addons-dataset download -d 2026-01-01
anki-addons-dataset ai
anki-addons-dataset parse
anki-addons-dataset report
anki-addons-dataset bundle
anki-addons-dataset upload
```

Operations can also be chained in a single command, running in the given order:

```bash
anki-addons-dataset init download -d 2026-01-01 ai parse
```

`ai` generates the one-sentence addon summaries. It is the only step that costs money, and it is
separate from `download` so that changing the prompt re-runs the AI calls alone. It reads the
snapshots already in `history/`, so it needs no `-d`, and it caches every answer under
`1-raw/4-ai/`; `parse` then picks the summaries out of that cache without any network access.

Against the default DeepSeek endpoint, `ai` refuses to run during DeepSeek's peak hours
(01:00-04:00 and 06:00-10:00 UTC, Monday through Friday), when the rate is double the off-peak
one, and fails with an error naming the window. Chinese public holidays are ignored: they only
turn peak hours into off-peak ones, so the check never lets a peak-rate request through.

`download` scrapes AnkiWeb with a headless browser. Two timeouts (in seconds) can be raised on a slow
network:

```bash
anki-addons-dataset download -d 2026-01-01 --page-load-timeout 180 --element-wait-timeout 30
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--page-load-timeout` | 120 | how long a single page may take to load before the browser gives up |
| `--element-wait-timeout` | 120 | how long to wait for the page content to appear after loading |

### Sample runs

Testing a change against the whole dataset is slow: thousands of addon pages per snapshot, and the
whole history re-parsed. Two limits cut a run down to a slice of it, and combine freely:

```bash
anki-addons-dataset download -d 2026-01-01 -w ~/anki-addons-scratch --sample-addons 20
anki-addons-dataset parse report bundle -w ~/anki-addons-scratch
```

| Option | Meaning |
| --- | --- |
| `--sample-addons` | download and parse only the first N addons, ordered by addon id |
| `--sample-snapshots` | let `ai`/`parse`/`report`/`bundle` process only the newest N snapshots |

Use them with `-w` so a sampled run lands in a scratch working directory instead of the real one.
`download` records the addon limit in the snapshot, so a later `parse`/`ai`/`report` in its own
invocation applies the same limit without the flag being repeated.

A sampled run never uploads: `upload` on its own is rejected, and `all` runs through `bundle` and
skips it, so a partial dataset cannot reach HuggingFace.

## Configuration

Paths, credentials locations, the HuggingFace target and logging can be set in an optional YAML file
at `~/.anki-addons-dataset.yaml` (or elsewhere, via `-c/--config`). Every key is optional; omitted
keys keep the defaults shown below, and with no file at all the defaults apply:

```yaml
working_dir: ~/anki-addons-dataset       # where snapshots and the bundle are kept; -w overrides it
github:
  token_file: ~/.github/token.txt        # GitHub personal access token, read by download/parse
ai:
  endpoint: https://api.deepseek.com     # any OpenAI-compatible endpoint, used by the ai step
  api_key_file: ~/.config/anki-addons-dataset/deepseek-api-key.txt
  model: deepseek-flash
  readme_max_chars: 8000                 # the README is cut to this length before entering the prompt
huggingface:
  repo_id: Ya-Alex/anki-addons           # the dataset upload targets
  synced_dirs: [history, latest]         # the remote folders upload pushes and prunes
logging:
  level: INFO                            # console level; the log file always gets DEBUG
  format: '%(asctime)-15s %(levelname)-8s [%(threadName)-10s] %(message)s'
  file: logs/anki-addons-dataset.log     # relative to working_dir; `false` disables file logging
sample:
  addons: null                           # only the first N addons by id; --sample-addons overrides it
  snapshots: null                        # only the newest N snapshots; --sample-snapshots overrides it
```

`~` and `$VAR` are expanded in path values. An unknown or misspelled key is an error rather than a
silent no-op, so typos surface immediately.

Values resolve as **CLI flag > config file > default**: `-l WARNING` overrides `logging.level` and
`-w/--working-dir` overrides `working_dir`, `--sample-addons`/`--sample-snapshots` override the
`sample` section, but the file still applies when a flag is absent. The
`info` step prints the resolved values.

```bash
anki-addons-dataset init download -d 2026-01-01 -w ~/anki-addons-scratch
```

The HuggingFace token is not part of this file — `huggingface_hub` reads it from `HF_TOKEN` or from
`hf auth login`.

## Links
- [Visualizations](https://huggingface.co/spaces/Ya-Alex/anki-addons) in HuggingFace Spaces
- [HuggingFace Dataset](https://huggingface.co/datasets/Ya-Alex/anki-addons)
- [Developer Guide](README-DEV.md)
- [Sonar Qube](https://sonarcloud.io/project/overview?id=Aleks-Ya_anki-addons-dataset)
- Anki
    - [Anki home page](https://apps.ankiweb.net)
    - [Anki Addons catalog](https://ankiweb.net/shared/addons)

[![Unit-tests](https://github.com/Aleks-Ya/anki-addons-dataset/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/Aleks-Ya/anki-addons-dataset/actions/workflows/unit-tests.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Aleks-Ya_anki-addons-dataset&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Aleks-Ya_anki-addons-dataset)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=Aleks-Ya_anki-addons-dataset&metric=coverage)](https://sonarcloud.io/summary/new_code?id=Aleks-Ya_anki-addons-dataset)
