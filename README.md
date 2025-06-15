# Anki Addons Dataset

## Setup Python virtual environment
1. Install PyEnv: `brew install pyenv pyenv-virtualenv`
2. Create virtual environment:
    1. `pyenv install 3.13.5`
    2. `pyenv virtualenv 3.13.5 anki-addons-dataset`
3. Install Anki packages
    1. Activate virtual environment: `pyenv activate anki-addons-dataset`
    2. Install packages: `pip install -U -r requirements.txt`

## Unit-test
Run: `pytest`

## Create the dataset
Run: `addon_catalog.py`
