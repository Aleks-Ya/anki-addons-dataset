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

## Create a new version
1. Generate the dataset dir: `python addon_catalog.py`
2. Upload the dataset dir as a new version:
   `kaggle datasets version -p $HOME/anki-addons-dataset/dataset -m "Update" -r zip`
