# Developer Guide

## Setup Python virtual environment
1. Install PyEnv: `brew install pyenv pyenv-virtualenv`
2. Create virtual environment:
    1. `pyenv install 3.13.5`
    2. `pyenv virtualenv 3.13.5 anki-addons-dataset`
3. Install Anki packages
    1. Activate virtual environment: `pyenv activate anki-addons-dataset`
    2. Install packages: `pip install -U -r requirements.txt`

## Unit-test
Run locally: `pytest`  
Unit-tests are automatically executed in GitHub Actions.

## Create a new version
1. Generate the dataset dir: `PYTHONPATH=src python -m anki_addons_dataset.addon_catalog --creation-date 2025-06-20`
2. Upload the dataset dir as a new version: `huggingface-cli upload-large-folder Ya-Alex/anki-addons $HOME/anki-addons-dataset/dataset --repo-type=dataset --num-workers=4`
3. Create a version Git tag:
    1. (Repo is cloned: `git clone https://huggingface.co/datasets/Ya-Alex/anki-addons`)
    2. Pull the latest commit: `git pull`
    3. Create a tag: `git tag v1_2025-06-24`
    4. Push the tag: `git push --tags`

## Sonar Qube
https://sonarcloud.io/project/overview?id=Aleks-Ya_anki-addons-dataset  
Sonar report is automatically updated in GitHub Actions.