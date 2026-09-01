# Anki Addons Dataset

A HuggingFace dataset of addons for the [Anki](https://apps.ankiweb.net) flashcard program.

## Install

```bash
pip install anki-addons-dataset
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install anki-addons-dataset   # install the command
uvx anki-addons-dataset info          # or run it once, without installing
```

This installs the `anki-addons-dataset` command. The pipeline runs as a sequence of operations:

```bash
anki-addons-dataset info
anki-addons-dataset init
anki-addons-dataset download -d 2026-01-01
anki-addons-dataset parse
anki-addons-dataset report
anki-addons-dataset bundle
anki-addons-dataset upload
```

Operations can also be chained in a single command, running in the given order:

```bash
anki-addons-dataset init download -d 2026-01-01 parse
```

`download` scrapes AnkiWeb with a headless browser. Two timeouts (in seconds) can be raised on a slow
network:

```bash
anki-addons-dataset download -d 2026-01-01 --page-load-timeout 180 --element-wait-timeout 30
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--page-load-timeout` | 120 | how long a single page may take to load before the browser gives up |
| `--element-wait-timeout` | 120 | how long to wait for the page content to appear after loading |

## Links
- [Visualizations](https://huggingface.co/spaces/Ya-Alex/anki-addons) in HuggingFace Spaces
- [HuggingFace Dataset](https://huggingface.co/datasets/Ya-Alex/anki-addons)
- [Developer Guide](README-DEV.md)
- [Sonar Qube](https://sonarcloud.io/project/overview?id=Aleks-Ya_anki-addons-dataset)
- Anki
    - [Anki home page](https://apps.ankiweb.net)
    - [Anki Addons catalog](https://ankiweb.net/shared/addons)

[![Unit-tests](https://github.com/Aleks-Ya/anki-addons-dataset/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/Aleks-Ya/anki-addons-dataset/actions/workflows/unit-tests.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Aleks-Ya_anki-addons-dataset&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Aleks-Ya_anki-addons-dataset)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=Aleks-Ya_anki-addons-dataset&metric=coverage)](https://sonarcloud.io/summary/new_code?id=Aleks-Ya_anki-addons-dataset)
