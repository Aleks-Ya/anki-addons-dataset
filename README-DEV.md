# Developer Guide

## Set up a Python virtual environment
The project is managed by [uv](https://docs.astral.sh/uv/).

1. Install uv: `brew install uv`
2. Create the virtual environment and install all dependencies: `uv sync`

`uv sync` creates `.venv/` using the Python version pinned in `.python-version` (downloading that
interpreter if needed), installs the project in editable mode, and installs the `dev` dependency
group — all resolved from the committed `uv.lock`, so every machine gets identical versions.

Prefix commands with `uv run` (e.g. `uv run pytest`) to use that environment without activating it,
or activate it the usual way with `source .venv/bin/activate`.

Upgrade all dependencies to their latest allowed versions (refreshes `uv.lock`): `./uv_update.sh`

## Unit-test
Run locally: `uv run pytest`  
Unit-tests are automatically executed in GitHub Actions.  
All external services are mocked, so the whole suite runs without network access.

## Integration tests
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

## GitHub
https://github.com/Aleks-Ya/anki-addons-dataset

## Sonar Qube
https://sonarcloud.io/project/overview?id=Aleks-Ya_anki-addons-dataset  
Sonar report is automatically updated in GitHub Actions.

## HuggingFace CLI
1. Login: `hf auth login`
2. Verify: `hf auth whoami`

## HuggingFace Spaces
Visualizations: https://huggingface.co/spaces/Ya-Alex/anki-addons

The Space downloads the dataset parquet files from the Hub on startup and logs:

```
Warning: You are sending unauthenticated requests to the HF Hub.
Please set a HF_TOKEN to enable higher rate limits and faster downloads.
```

It is harmless: the dataset is public, so anonymous downloads work. The warning only means the Space
container has no `HF_TOKEN`, hence per-IP rate limits and no accelerated downloads. To silence it, add a
read-only token as a Space secret named `HF_TOKEN` (Space -> Settings -> Variables and secrets);
`huggingface_hub` reads it from the environment, no code change needed. This is unrelated to the
credentials `upload` uses (`hf auth login`).

## Configuration file
An optional `~/.anki-addons-dataset.yaml` supplies the working directory, the GitHub token path, the
AI provider, the HuggingFace target and the logging settings. See the *Configuration* section of [README.md](README.md)
for the full annotated example; `config.yaml.example` in the repo root is a copy-ready version:

```bash
cp config.yaml.example ~/.anki-addons-dataset.yaml
```

Values resolve as **CLI flag > config file > default**, and a different file can be passed with
`-c/--config`. The file deliberately lives outside the working directory, because the working
directory is itself one of its keys.

Pointing `working_dir` at a scratch directory and `huggingface.repo_id` at a personal scratch
dataset is the safe way to try the pipeline without touching the published one. A single run can be
redirected without touching the file at all — `-w/--working-dir` overrides `working_dir`, and the
`info` step prints the directory actually in use:

```bash
uv run anki-addons-dataset init -w ~/anki-addons-scratch
```

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

## AI summaries
The `ai` step generates the one-sentence addon summary exported as `ai.summary`. It is the only step
that spends money, so it is separate from `download`: it reads the snapshots already in `history/`
(no `-d`), builds a prompt from the addon title, the AnkiWeb description and the GitHub README, and
writes every answer to `history/<date>/1-raw/4-ai/ai-cache.jsonl`. `parse` then reads that cache
offline and attaches the summaries to the dump; an addon with no cached answer simply gets no
summary, and `parse` logs how many were missing.

The cache key is a hash of the model and the whole prompt, so editing the prompt template or
`ai.readme_max_chars` invalidates every entry. That is why the step stands on its own — refilling
the cache costs AI tokens rather than a full re-scrape. Answers are carried forward from the
previous snapshot when the prompt is unchanged, so a steady-state run only pays for addons whose
text actually moved.

`1-raw/` is bundled into `raw.zip` and published, so the cache is part of the public dataset. That is
what lets `init` restore it on a fresh machine. Each line holds the model, the answer and a SHA-256
of the prompt; the prompt text itself is not stored.

```bash
anki-addons-dataset ai            # all snapshots; watch the per-snapshot hit/miss counts
```

## Logging
Default log level: INFO (`logging.level` in the config file)
Set log level: `uv run anki-addons-dataset parse -l DEBUG` — the flag wins over the config file.
The log format and an optional log file are set by `logging.format` and `logging.file`.

## Browser timeouts
`download` drives a headless Chrome via Selenium. Both of its timeouts (seconds) are configurable and
are printed by the `info` step:

- `--page-load-timeout` (default 120): passed to `driver.set_page_load_timeout()`, aborts a hung page load
- `--element-wait-timeout` (default 120): passed to `WebDriverWait`, waits for the page content to appear

```bash
uv run anki-addons-dataset download -d 2026-01-01 --page-load-timeout 180 --element-wait-timeout 30
```

## Running the pipeline

The pipeline has seven steps run in order: `init download ai parse report bundle upload`.
There is also an `info` step that logs the app version and runtime configuration (working dir, HuggingFace dataset, GitHub token file, Python/platform, snapshot/report dates, browser timeouts) without side effects. It fails fast on bad credentials: a GitHub token that is absent, empty or
rejected by the API, an absent or empty AI API key file, or missing HuggingFace write access. The
GitHub and HuggingFace checks need network access; the AI key is only checked for presence, because a
live request would be billed on every `info` run.

A single invocation accepts any subset of steps (space-separated), or the shorthand `all`,
which expands to `info` followed by the full seven-step sequence in pipeline order:

```bash
anki-addons-dataset all -d 2026-01-01          # equivalent to: info init download ai parse report bundle upload
anki-addons-dataset parse report               # run only the given steps
anki-addons-dataset info                        # just print version and configuration
```

There are three ways to run it, depending on which version you need, plus a sampled run for
testing a change quickly:

### 1. Full run on a release version (from PyPI)

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

### 2. Given steps on a release version (from PyPI)

```bash
uvx anki-addons-dataset parse report                                   # latest release
uvx --from anki-addons-dataset==1.3.0 anki-addons-dataset parse report  # pinned release
```

### 3. Given steps on the current working source

`uv sync` installs the project in editable mode, so `uv run` executes your working tree:
```bash
uv run anki-addons-dataset parse report
```

Or run the source explicitly without relying on the install:
```bash
PYTHONPATH=src python -m anki_addons_dataset.addon_catalog parse report
```

### 4. Sample run: a slice of the dataset
Testing a change end-to-end against the real working directory means thousands of addon pages per
snapshot and the whole history re-parsed. `--sample-addons` and `--sample-snapshots` cut that down to
a slice; point `-w` at a scratch directory so the real one is never touched:

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

`--sample-snapshots N` limits `ai`/`parse`/`report`/`bundle` to the newest N snapshots, which is the
axis that matters once the scratch directory holds several dates.

A sampled run refuses to `upload`, so a partial dataset cannot reach HuggingFace. See the *Sample
runs* section of [README.md](README.md) for the user-facing description.

## Create a new version of HuggingFace dataset **from sources** by steps
1. Upgrade Python packages: `./uv_update.sh`
2. Check version: `uv run anki-addons-dataset info`
3. Initialize a working directory: `uv run anki-addons-dataset init` (creates `~/anki-addons-dataset`)
4. Download new snapshot: `uv run anki-addons-dataset download -d 2026-01-01` (creates `~/anki-addons-dataset/history/2026-01-01/1-raw`)
5. Parse dataset: `uv run anki-addons-dataset parse` (enriches `~/anki-addons-dataset/history/YYYY-MM-DD/2-stage`)
6. Generate reports: `uv run anki-addons-dataset report` (creates `~/anki-addons-dataset/history/YYYY-MM-DD/3-final`)
7. Create a bundle: `uv run anki-addons-dataset bundle` (creates `~/anki-addons-dataset/bundle`)
8. Upload the bundle: `uv run anki-addons-dataset upload` (syncs `~/anki-addons-dataset/bundle` to HuggingFace)
9. Restart the visualization space: https://huggingface.co/spaces/Ya-Alex/anki-addons
   (its startup log warns about `HF_TOKEN`, see [HuggingFace Spaces](#huggingface-spaces))
10. Post on Anki Forum: https://forums.ankiweb.net/t/anki-addons-dataset-a-detailed-list-of-addons/63090

## Release a new version of this repository
1. Checkout branch `main`
2. Pass Sonar Qube analysis (skill `/push`):
    1. Upgrade Python packages: `./uv_update.sh`
    2. Execute unit-tests: `uv run pytest`
    3. Push changes: `git push`
    4. Review GitHub Actions: https://github.com/Aleks-Ya/anki-addons-dataset/actions
    5. Review Sonar Qube report: https://sonarcloud.io/summary/overall?id=Aleks-Ya_anki-addons-dataset&branch=main
3. Increment version:
    1. Show the next versions: `uv run bump-my-version show-bump`
    2. Switch dev version to RELEASE (`0.1.1.dev0` -> `0.1.1`): `uv run bump-my-version bump release --tag`
    3. Switch the RELEASE version to the next dev (`0.1.1` -> `0.2.0.dev0`): `uv run bump-my-version bump minor`
4. Create a GitHub release (skill `/release`):
    1. Push branch and tags: `git push origin HEAD --tags`
    2. Create a release from the tag: https://github.com/Aleks-Ya/anki-addons-dataset/releases
    3. Wait for GitHub Actions to finish publishing to PyPI: https://github.com/Aleks-Ya/anki-addons-dataset/actions
    4. Verify the version: `uvx --refresh anki-addons-dataset info`

## Publish to PyPI
PyPi package: https://pypi.org/project/anki-addons-dataset

Publishing is automated: creating a GitHub release runs `.github/workflows/publish.yml`
(PyPI Trusted Publishing, no API tokens).

One-time setup on [pypi.org](https://pypi.org/manage/account/publishing/): add a Trusted Publisher for
this project pointing at repo `Aleks-Ya/anki-addons-dataset`, workflow `publish.yml`, environment
`pypi` (add it as a "pending publisher" before the first release).

Manual build/publish (fallback):
```bash
uv build                   # creates dist/*.whl and dist/*.tar.gz
uv publish                 # requires a PyPI API token (UV_PUBLISH_TOKEN)
```
Note: builds from a `.dev0` checkout produce a development version; only released (non-`.dev`) tags
yield a clean PyPI version.
