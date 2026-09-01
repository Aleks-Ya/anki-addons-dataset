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

## GitHub
https://github.com/Aleks-Ya/anki-addons-dataset

## Sonar Qube
https://sonarcloud.io/project/overview?id=Aleks-Ya_anki-addons-dataset  
Sonar report is automatically updated in GitHub Actions.

## HuggingFace CLI
1. Login: `hf auth login`
2. Verify: `hf auth whoami`

## GitHub token
The `download` and `parse` steps call the GitHub REST API and need a personal access token
(no scopes required for public repositories) in `~/.github/token.txt`:

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
Default log level: DEBUG
Set log level: `uv run anki-addons-dataset parse -l INFO`

## Browser timeouts
`download` drives a headless Chrome via Selenium. Both of its timeouts (seconds) are configurable and
are printed by the `info` step:

- `--page-load-timeout` (default 60): passed to `driver.set_page_load_timeout()`, aborts a hung page load
- `--element-wait-timeout` (default 10): passed to `WebDriverWait`, waits for the page content to appear

```bash
uv run anki-addons-dataset download -d 2026-01-01 --page-load-timeout 120 --element-wait-timeout 30
```

## Running the pipeline

The pipeline has six steps run in order: `init download parse report bundle upload`.
There is also an `info` step that logs the app version and runtime configuration (working dir, HuggingFace dataset, GitHub token file, Python/platform, snapshot/report dates, browser timeouts) without side effects. It fails fast on bad credentials: a GitHub token that is absent, empty or
rejected by the API, or missing HuggingFace write access. Both checks need network access.

A single invocation accepts any subset of steps (space-separated), or the shorthand `all`,
which expands to `info` followed by the full six-step sequence in pipeline order:

```bash
anki-addons-dataset all -d 2026-01-01          # equivalent to: info init download parse report bundle upload
anki-addons-dataset parse report               # run only the given steps
anki-addons-dataset info                        # just print version and configuration
```

There are three ways to run it, depending on which version you need:

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
