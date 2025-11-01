# Developer Guide

## Setup Python virtual environment
1. Install PyEnv: `brew install pyenv pyenv-virtualenv`
2. Create virtual environment:
    1. `pyenv install 3.14.0`
    2. `pyenv virtualenv 3.14.0 anki-addons-dataset`
3. Install Anki packages
    1. Activate virtual environment: `pyenv activate anki-addons-dataset`
    2. Install packages: `pip install -U -r requirements.txt`

## Unit-test
Run locally: `pytest`  
Unit-tests are automatically executed in GitHub Actions.

## Create a new version
1. Check out the latest Git tag: `git checkout v0.6.0`
2. Download dataset: `PYTHONPATH=src python -m anki_addons_dataset.addon_catalog download -d 2025-11-01` (creates dir `~/anki-addons-dataset/history/2025-11-01`)
3. Parse dataset: `PYTHONPATH=src python -m anki_addons_dataset.addon_catalog parse -d 2025-11-01` (creates dir `~/anki-addons-dataset/dataset`)
4. Upload the dataset dir as a new version: `huggingface-cli upload-large-folder Ya-Alex/anki-addons $HOME/anki-addons-dataset/dataset --repo-type=dataset --num-workers=4`
5. Delete unused files from the remote repo manually (`huggingface-cli` just updates files)

## Sonar Qube
https://sonarcloud.io/project/overview?id=Aleks-Ya_anki-addons-dataset  
Sonar report is automatically updated in GitHub Actions.

## Version
Show the next versions: `bump-my-version show-bump`
Increment SNAPSHOT version (`0.1.1-SNAPSHOT` -> `0.2.0-SNAPSHOT`): `bump-my-version bump minor`
Switch SNAPSHOT version to RELEASE (`0.1.1-SNAPSHOT` -> `0.1.1`): `bump-my-version bump release`
Switch RELEASE version to SNAPSHOT (`0.1.1` -> `0.2.0-SNAPSHOT`): `bump-my-version bump minor`