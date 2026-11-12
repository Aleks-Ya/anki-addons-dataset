# Versioning

The dataset has its own version, `MAJOR.MINOR`, independent of the version of the code that builds it. Every
snapshot's `metadata.json` records it as `dataset_version`. Back to the
[dataset card](https://huggingface.co/datasets/Ya-Alex/anki-addons).

- **MAJOR** goes up on a breaking change to anything published: a table, config, column or file path is removed
  or renamed, a column's type changes, or a value's meaning changes.
- **MINOR** goes up on an additive change: a new table, config, column, file or value.
- A new snapshot, or the history regenerated without a schema change, changes neither.

Every upload regenerates `history/` too, so all snapshots in one revision share one schema.

## Revisions
| Revision                                    | Updated                                                   | Use it for                               |
|---------------------------------------------|-----------------------------------------------------------|------------------------------------------|
| `main`                                      | every upload                                              | always the newest, may break             |
| branch `v1`, `v2`, ...                      | every upload while that MAJOR is current, then frozen      | new data without breaking changes        |
| tag `v1.0-2026-11-01` (version-snapshot)    | never; a re-upload of the same snapshot adds `-2`, `-3`... | reproducing a result exactly             |

```python
from datasets import load_dataset
import pandas as pd

addons = load_dataset("Ya-Alex/anki-addons", revision="v1", split="train")
addons = pd.read_parquet("hf://datasets/Ya-Alex/anki-addons@v1/latest/parquet/data.parquet")
```

What changed in each version: [changelog.md](changelog.md).

## For maintainers
`DATASET_VERSION` in `src/anki_addons_dataset/common/data_types.py` is the version, and
[schema.json](schema.json) records the published Parquet columns. The `data` columns and their types come from
the `Details` dataclasses in `json_addon_info.py` (`ArrowSchema`), so an empty column keeps its type. `dataset_schema_test.py` fails when the
columns change, names the version to bump to and prints the new `schema.json`. A change of meaning shows no
schema change, so bump MAJOR for it by hand and update the version in `schema.json`.

UPLOAD pushes to `main`, then tags the new head and points the `v{MAJOR}` branch at it.
