---
license: cc0-1.0
language:
  - en
pretty_name: Anki Addons Dataset
size_categories:
  - 10K<n<100K
tags:
  - anki
  - addon
---

## Introduction

[Anki flashcard program](https://apps.ankiweb.net) has about [2 thousand addons](https://ankiweb.net/shared/addons).  
This dataset contains information about these addons including data from
the [Addon Catalog](https://ankiweb.net/shared/addons), [GitHub](https://github.com),
and [Anki Forum](https://forums.ankiweb.net).

---

## Files
### Excel
The best for **manual analysis** in Microsoft Excel or LibreOffice Calc.  
Location: `structured/xlsx/data.xlsx`

### JSON
The best for **programmatic analysis** by Python, etc.  
The JSON file contains all parsed fields. The Excel and Markdown files contain part of its fields.  
Location: `structured/json/data.json`  
JSON schema: `structured/json/schema.json`

### Markdown
Location: `structured/markdown/data.md`

---

## Raw data
Raw data (collected during the dataset construction) are available in the `raw` folder.  
It includes HTML pages of the Addon Catalog, responses of GitHub REST API,
and intermediate files generated from them.  
File `raw/4-overrider/overrides.yaml` contains manually curated data which override automatically parsed values.

Structure of the `raw` folder:
- `1-anki-web`/
    - `1-html`/
        - `addons.html`
        - `addon`/
            - `{addon-id}.html`
    - `2-json`/`addon`/
        - `{addon-id}.json`
- `2-github`/`{user}`/`{repo}`/
    - `{repo}_action-count.json`
    - `{repo}_languages.json`
    - `{repo}_last-commit.json`
    - `{repo}_stars-count.json`
    - `{repo}_tests-count.json`
- `3-enricher`/ `addon`/
    - `{addon-id}.json`
- `4-overrider`/
    - `overrides.yaml`

---

## Source code
Python code that generated this dataset is available in [anki-addons-dataset](https://github.com/Aleks-Ya/anki-addons-dataset) GitHub repo.
