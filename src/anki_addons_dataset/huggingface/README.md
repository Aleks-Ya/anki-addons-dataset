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
configs:
  - config_name: default
    data_files: latest/parquet/data.parquet
---

## Introduction

[Anki flashcard program](https://apps.ankiweb.net) has more than [2 thousand addons](https://ankiweb.net/shared/addons).  
This dataset contains information about these addons including data from
the [Addon Catalog](https://ankiweb.net/shared/addons), [GitHub](https://github.com/Aleks-Ya/anki-addons-dataset), and [Anki Forum](https://forums.ankiweb.net).  
Usually, the dataset is updated once a month.

Questions, feedback, bugs: [Support page at Anki Forum](https://forums.ankiweb.net/t/anki-addons-dataset-a-detailed-list-of-addons/63090)

---

## Visualization
See [HuggingFace Spaces app](https://huggingface.co/spaces/Ya-Alex/anki-addons)

## Files
### Structure
Folder `history` contains data files for each day when the dataset was updated.  
Folder `latest` contains the most recent day from `history`.
```
├── history
│   ├── YYYY-MM-DD
│   │   ├── json
│   │   │   ├── aggregation.json
│   │   │   ├── data.json
│   │   │   └── schema.json
│   │   ├── parquet
│   │   │   ├── aggregation.parquet
│   │   │   └── data.parquet
│   │   ├── xlsx
│   │   │   ├── aggregation.xlsx
│   │   │   └── data.xlsx
│   │   ├── metadata.json
│   │   ├── raw.zip
│   │   └── stage.zip
├── latest
│   ├── json
│   │   ├── aggregation.json
│   │   ├── data.json
│   │   └── schema.json
│   ├── parquet
│   │   ├── aggregation.parquet
│   │   └── data.parquet
│   ├── xlsx
│   │   ├── aggregation.xlsx
│   │   └── data.xlsx
│   └── metadata.json
└── README.md
```

### Excel
The best for **manual analysis** in Microsoft Excel or LibreOffice Calc.  
Location: `latest/xlsx/data.xlsx`, `history/YYYY-MM-DD/xlsx/data.xlsx`

### Parquet
The best for **programmatic analysis** by Python, etc.  
Location: `latest/parquet/data.parquet`, `history/YYYY-MM-DD/xlsx/data.xlsx`

### JSON
Exported from the Parquet file.   
Location: `latest/json/data.json`  , `history/YYYY-MM-DD/json/data.json`  
JSON schema: `latest/json/schema.json`, `history/YYYY-MM-DD/json/schema.json`

---

## Raw and Stage data
Raw data (collected during the dataset construction) are available in `history/YYYY-MM-DD/raw.zip`.  
It includes HTML pages of the Addon Catalog, responses of GitHub REST API, and responses of Anki Forum API.  
Structure of the raw data:
```
raw-metadata.json
1-anki-web/
    addons_page.html
    addon/{addon-id}.html
2-github/{user}/{repo}/
    actions.json
    info.json
    languages.json
    last-commit.json
    tree.json
3-forum/topic/{topic_id}.json
```

Stage data (intermediate data generated during the dataset construction) are available in `history/YYYY-MM-DD/stage.zip`.  
File `4-overrider/overrides.yaml` contains manually curated data which override automatically parsed values.  
Structure of the stage data:
```
1-anki-web/addon/{addon-id}.html
2-github/{user}/{repo}/
    action-count.json
    languages.json
    last-commit.json
    stars-count.json
    tests-count.json
3-enricher/
    forum/{addon-id}.json
    github/{addon-id}.json
4-overrider/overrides.yaml
```

---

## Source code
Python code that generated this dataset is available in [anki-addons-dataset](https://github.com/Aleks-Ya/anki-addons-dataset) GitHub repo.
