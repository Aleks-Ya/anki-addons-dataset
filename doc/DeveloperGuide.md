# Developer Guide

## Setup Python virtual environment
1. Install PyEnv: `brew install pyenv pyenv-virtualenv`
2. Create virtual environment:
    1. `pyenv install 3.14.2`
    2. `pyenv virtualenv 3.14.2 anki-addons-dataset`
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

## Create a new version of HuggingFace dataset
1. Upgrade Python packages: `./pip_update.sh`
2. Check out the latest Git tag: `git checkout v0.8.0`
3. Download dataset: `PYTHONPATH=src python -m anki_addons_dataset.addon_catalog download -d 2026-01-01` (creates dir `~/anki-addons-dataset/history/2026-01-01`)
4. Parse dataset: `PYTHONPATH=src python -m anki_addons_dataset.addon_catalog parse` (enriches all versions in `~/anki-addons-dataset/history`)
5. Create a bundle: `PYTHONPATH=src python -m anki_addons_dataset.addon_catalog bundle` (creates dir `~/anki-addons-dataset/bundle`)
6. Upload
    1. Delete old files: `hf repo-files delete --repo-type=dataset Ya-Alex/anki-addons '*'`
    2. Upload new files: `hf upload-large-folder --repo-type=dataset Ya-Alex/anki-addons $HOME/anki-addons-dataset/bundle`
7. Post on Anki Forum: https://forums.ankiweb.net/t/anki-addons-dataset-a-detailed-list-of-addons/63090
8. Restart the visualization space: https://huggingface.co/spaces/Ya-Alex/anki-addons

## Release a new version of this repository
On branch `main`:
1. Upgrade Python packages: `./pip_update.sh`
2. Execute unit-tests: `pytest`
3. Pass Sonar Qube analysis:
    1. Push changes: `git push`
    2. Review GitHub Actions: https://github.com/Aleks-Ya/anki-addons-dataset/actions
    3. Review Sonar Qube report: https://sonarcloud.io/summary/overall?id=Aleks-Ya_anki-addons-dataset&branch=main
4. Increment version:
    1. Show the next versions: `bump-my-version show-bump`
    2. Switch SNAPSHOT version to RELEASE (`0.1.1-SNAPSHOT` -> `0.1.1`): `bump-my-version bump release --tag`
    3. Switch RELEASE version to SNAPSHOT (`0.1.1` -> `0.2.0-SNAPSHOT`): `bump-my-version bump minor`
5. Create a GitHub release:
    1. Push tags: `git push --tags`
    2. Create a release from the tag: https://github.com/Aleks-Ya/anki-addons-dataset/releases
