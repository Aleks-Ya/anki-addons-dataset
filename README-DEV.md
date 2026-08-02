# Developer Guide

## Set up a Python virtual environment
1. Install PyEnv: `brew install pyenv pyenv-virtualenv`
2. Create a virtual environment:
    1. `pyenv install 3.14.5`
    2. Delete old virtual environment (optional): `pyenv virtualenv-delete anki-addons-dataset`
    3. `pyenv virtualenv 3.14.5 anki-addons-dataset`
3. Install Anki packages
    1. Activate virtual environment: `pyenv activate anki-addons-dataset`
    2. Install packages: `./pip_update.sh`

## Unit-test
Run locally: `pytest`  
Unit-tests are automatically executed in GitHub Actions.

## GitHub
https://github.com/Aleks-Ya/anki-addons-dataset

## Sonar Qube
https://sonarcloud.io/project/overview?id=Aleks-Ya_anki-addons-dataset  
Sonar report is automatically updated in GitHub Actions.

## HuggingFace CLI
1. Login: `hf auth login`
2. Verify: `hf auth whoami`

## Logging
Default log level: DEBUG
Set log level: `PYTHONPATH=src python -m anki_addons_dataset.addon_catalog parse -l INFO`

## Running the pipeline

The pipeline has six steps run in order: `init download parse report bundle upload`.
There is also an `info` step that just logs the app version and runtime configuration (working dir, HuggingFace dataset, Python/platform, snapshot/report dates) without side effects.

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

Activate the editable dev env and the same command runs your working tree:
```bash
pyenv activate anki-addons-dataset
anki-addons-dataset parse report
```

Or run the source explicitly without relying on the install:
```bash
PYTHONPATH=src python -m anki_addons_dataset.addon_catalog parse report
```

## Create a new version of HuggingFace dataset **from sources** by steps
1. Upgrade Python packages: `./pip_update.sh`
2. Check version: `PYTHONPATH=src python -m anki_addons_dataset.addon_catalog info`
3. Initialize a working directory: `PYTHONPATH=src python -m anki_addons_dataset.addon_catalog init` (creates `~/anki-addons-dataset`)
4. Download new snapshot: `PYTHONPATH=src python -m anki_addons_dataset.addon_catalog download -d 2026-01-01` (creates `~/anki-addons-dataset/history/2026-01-01/1-raw`)
5. Parse dataset: `PYTHONPATH=src python -m anki_addons_dataset.addon_catalog parse` (enriches `~/anki-addons-dataset/history/YYYY-MM-DD/2-stage`)
6. Generate reports: `PYTHONPATH=src python -m anki_addons_dataset.addon_catalog report` (creates `~/anki-addons-dataset/history/YYYY-MM-DD/3-final`)
7. Create a bundle: `PYTHONPATH=src python -m anki_addons_dataset.addon_catalog bundle` (creates `~/anki-addons-dataset/bundle`)
8. Upload the bundle: `PYTHONPATH=src python -m anki_addons_dataset.addon_catalog upload` (syncs `~/anki-addons-dataset/bundle` to HuggingFace)
9. Restart the visualization space: https://huggingface.co/spaces/Ya-Alex/anki-addons
10. Post on Anki Forum: https://forums.ankiweb.net/t/anki-addons-dataset-a-detailed-list-of-addons/63090

## Release a new version of this repository
1. Checkout branch `main`
2. Pass Sonar Qube analysis (skill `/push`):
    1. Upgrade Python packages: `./pip_update.sh`
    2. Execute unit-tests: `pytest`
    3. Push changes: `git push`
    4. Review GitHub Actions: https://github.com/Aleks-Ya/anki-addons-dataset/actions
    5. Review Sonar Qube report: https://sonarcloud.io/summary/overall?id=Aleks-Ya_anki-addons-dataset&branch=main
3. Increment version:
    1. Show the next versions: `bump-my-version show-bump`
    2. Switch dev version to RELEASE (`0.1.1.dev0` -> `0.1.1`): `bump-my-version bump release --tag`
    3. Switch the RELEASE version to the next dev (`0.1.1` -> `0.2.0.dev0`): `bump-my-version bump minor`
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
pip install build twine
python -m build            # creates dist/*.whl and dist/*.tar.gz
twine check dist/*
twine upload dist/*        # requires a PyPI API token
```
Note: builds from a `.dev0` checkout produce a development version; only released (non-`.dev`) tags
yield a clean PyPI version.
