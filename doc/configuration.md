# Configuration

## Configuration file
Paths, credentials locations, the AI provider, the HuggingFace target and logging can be set in an
optional YAML file at `~/.anki-addons-dataset.yaml` (or elsewhere, via `-c/--config`). Every key is
optional; omitted keys keep the defaults shown below, and with no file at all the defaults apply:

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
  file: logs/anki-addons-dataset.log     # name template; relative to working_dir, `false` disables file logging
  keep: 30                               # delete all but the newest N run logs; `false` keeps them all
sample:
  addons: null                           # only the first N addons by id; --sample-addons overrides it
  snapshots: null                        # only the newest N snapshots; --sample-snapshots overrides it
```

`config.yaml.example` in the repo root is a copy-ready version:

```bash
cp config.yaml.example ~/.anki-addons-dataset.yaml
```

`~` and `$VAR` are expanded in path values. An unknown or misspelled key is an error rather than a
silent no-op, so typos surface immediately.

Values resolve as **CLI flag > config file > default**: `-l WARNING` overrides `logging.level`,
`-w/--working-dir` overrides `working_dir`, and `--sample-addons`/`--sample-snapshots` override the
`sample` section, but the file still applies when a flag is absent. The `info` step prints the
resolved values. The file deliberately lives outside the working directory, because the working
directory is itself one of its keys.

Pointing `working_dir` at a scratch directory and `huggingface.repo_id` at a personal scratch
dataset is the safe way to try the pipeline without touching the published one. A single run can be
redirected without touching the file at all:

```bash
uv run anki-addons-dataset init download -d 2026-01-01 -w ~/anki-addons-scratch
```

The HuggingFace token is not part of this file — `huggingface_hub` reads it from `HF_TOKEN` or from
`hf auth login`.

## GitHub token
The `download` and `parse` steps call the GitHub REST API and need a personal access token
(no scopes required for public repositories) in `~/.github/token.txt` (or wherever
`github.token_file` points):

```bash
mkdir -p ~/.github
echo '<personal-access-token>' > ~/.github/token.txt
```

The `info` step validates the token against `https://api.github.com/rate_limit` (a request GitHub
does not count against the quota), so an absent, empty, expired or revoked token aborts `all`
immediately instead of failing minutes later during `download`. It also verifies HuggingFace
write access to the dataset (the same check `upload` runs), so both credentials are validated
up front.

## Logging
Default console log level: INFO (`logging.level` in the config file)
Set log level: `uv run anki-addons-dataset parse -l DEBUG` — the flag wins over the config file.
It only moves the console level: the log file always receives DEBUG.
Every run also writes its own log file under `<working_dir>/logs/`, so a run's output survives the
terminal and is never mixed with another run's: the start timestamp goes into the name, giving
`logs/anki-addons-dataset-2026-09-28-143005.log`. `logging.file` is the template the name is built
from (a relative path stays relative to the working directory) and `logging.file: false` turns file
logging off; `logging.keep` (30 by default, `false` for unlimited) deletes all but the newest N run
logs at startup; `logging.format` sets the format.
`init` leaves the log directory alone: it moves the other top-level entries of the working directory into
`backups/YYYYmmdd-HHMMSS/`, so the log of the run that re-initialized the working directory stays in
`<working_dir>/logs/` together with the earlier ones.

## Browser timeouts
`download` scrapes AnkiWeb with a headless Chrome driven by Selenium. Both of its timeouts (in
seconds) can be raised on a slow network and are printed by the `info` step:

| Option | Default | Meaning |
| --- | --- | --- |
| `--page-load-timeout` | 120 | passed to `driver.set_page_load_timeout()`; how long a single page may take to load before the browser gives up |
| `--element-wait-timeout` | 120 | passed to `WebDriverWait`; how long to wait for the page content to appear after loading |

```bash
uv run anki-addons-dataset download -d 2026-01-01 --page-load-timeout 180 --element-wait-timeout 30
```
