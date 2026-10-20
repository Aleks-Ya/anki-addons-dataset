# Developer Guide

## Documentation
- [Running the pipeline](doc/pipeline.md) — `-d`, release vs working source, sample runs
- [Configuration](doc/configuration.md) — config file, GitHub token, logging, browser timeouts
- [AI summaries and tags](doc/ai.md) — the `ai` step, its cache and costs
- [Anki versions](doc/anki-versions.md) — how addon version ranges are parsed
- [Integration tests](doc/testing.md) — live tests and their requirements
- [HuggingFace](doc/huggingface.md) — CLI login, the visualization Space
- [Publish to PyPI](doc/pypi.md) — automated and manual publishing
- [UML diagrams](doc/uml.md) — PlantUML sources in `doc/uml/`

## Install
The released command comes from PyPI:

```bash
pip install anki-addons-dataset
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install anki-addons-dataset   # install the command
uvx anki-addons-dataset info          # or run it once, without installing
```

Either way this provides the `anki-addons-dataset` command. To run the working sources instead, set
up the virtual environment below and prefix commands with `uv run`.

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
Integration tests: [doc/testing.md](doc/testing.md).

## Running the pipeline

The pipeline has seven steps run in order: `init download ai parse report bundle upload`.
There is also an `info` step that logs the app version and runtime configuration (working dir, HuggingFace dataset, GitHub token file, Python/platform, snapshot/report dates, browser timeouts) without side effects. It fails fast on bad credentials: a GitHub token that is absent, empty or
rejected by the API, an AI API key file that is absent, empty or rejected by the provider, or missing
HuggingFace write access. All three checks need network access: the AI one asks the configured endpoint
for the shortest possible answer, so it costs a handful of tokens per `info` run, and it reports the
remaining balance where the provider exposes it (DeepSeek does). Against DeepSeek the check also
inherits the peak-hour refusal, so run `info` outside the peak hours.

Each step can be run on its own:

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

A single invocation also accepts any subset of steps (space-separated), running them in the given
order, or the shorthand `all`, which expands to `info` followed by the full seven-step sequence in
pipeline order:

```bash
anki-addons-dataset init download -d 2026-01-01 ai parse
anki-addons-dataset all -d 2026-01-01          # equivalent to: info init download ai parse report bundle upload
anki-addons-dataset parse report               # run only the given steps
anki-addons-dataset info                       # just print version and configuration
```

Snapshot dates, ways to run a release or the working source, and sample runs: [doc/pipeline.md](doc/pipeline.md)

## Create a new version of HuggingFace dataset **from sources** by steps
1. Upgrade Python packages: `./uv_update.sh`
2. Check version: `uv run anki-addons-dataset info`
3. Initialize a working directory: `uv run anki-addons-dataset init` (creates `~/anki-addons-dataset`; any
   existing content except `logs/` is moved to `~/anki-addons-dataset/backups/YYYYmmdd-HHMMSS`)
4. Download new snapshot: `uv run anki-addons-dataset download -d 2026-01-01` (creates `~/anki-addons-dataset/history/2026-01-01/1-raw`)
5. Parse dataset: `uv run anki-addons-dataset parse` (enriches `~/anki-addons-dataset/history/YYYY-MM-DD/2-stage`)
6. Generate reports: `uv run anki-addons-dataset report` (creates `~/anki-addons-dataset/history/YYYY-MM-DD/3-final`)
7. Create a bundle: `uv run anki-addons-dataset bundle` (creates `~/anki-addons-dataset/bundle`)
8. Upload the bundle: `uv run anki-addons-dataset upload` (syncs `~/anki-addons-dataset/bundle` to HuggingFace)
9. Restart the visualization space: https://huggingface.co/spaces/Ya-Alex/anki-addons
   (its startup log warns about `HF_TOKEN`, see [HuggingFace Spaces](doc/huggingface.md#huggingface-spaces))
10. Post on Anki Forum: https://forums.ankiweb.net/t/anki-addons-dataset-a-detailed-list-of-addons/63090

## Release a new version of this repository
1. Checkout branch `main`
2. Pass Sonar Qube analysis (skill `/push`):
    1. Upgrade Python packages: `./uv_update.sh`
    2. Execute unit-tests: `uv run pytest`
    3. Push changes: `git push`
    4. Review GitHub Actions: https://github.com/Aleks-Ya/anki-addons-dataset/actions
    5. Review Sonar Qube report: https://sonarcloud.io/summary/overall?id=Aleks-Ya_anki-addons-dataset&branch=main
3. Increment the version and create a GitHub release (skill `/release`):
    1. Choose the next version from the latest release tag (`v2.3.0`): patch `2.3.1`, minor `2.4.0` or major `3.0.0`
    2. Bump to it and tag it: `uv run bump-my-version bump --new-version 2.4.0 --tag`
    3. Push branch and tags: `git push origin HEAD --tags`
    4. Create a release from the tag: https://github.com/Aleks-Ya/anki-addons-dataset/releases
    5. Wait for GitHub Actions to finish publishing to PyPI: https://github.com/Aleks-Ya/anki-addons-dataset/actions
    6. Verify the version: `uvx --refresh anki-addons-dataset info`
    7. Bump to the next development version and push: `uv run bump-my-version bump patch && git push`

Publishing to PyPI: [doc/pypi.md](doc/pypi.md).

## GitHub
https://github.com/Aleks-Ya/anki-addons-dataset

## Sonar Qube
https://sonarcloud.io/project/overview?id=Aleks-Ya_anki-addons-dataset  
Sonar report is automatically updated in GitHub Actions.
