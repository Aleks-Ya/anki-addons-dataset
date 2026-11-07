# Files

The layout of the [HuggingFace dataset](https://huggingface.co/datasets/Ya-Alex/anki-addons).

```
latest/                     the newest snapshot
    parquet/{table}.parquet
    xlsx/{table}.xlsx
    metadata.json
history/YYYY-MM-DD/         every snapshot, the same layout plus:
    raw.zip                 the collected source data: AnkiWeb pages, GitHub and Anki Forum API responses, AI answers
    stage.zip               intermediate data, including the manual corrections in 4-overrider/overrides.yaml
packages/{addon-id}/        the .ankiaddon files, each version once (package-list.json in raw.zip lists a snapshot's)
```

Parquet is best for code; Excel for manual analysis in Excel or LibreOffice Calc. The `reviews` and `packages`
tables are Parquet only. See [addon fields](addons.md) and [other tables](tables.md).

## License
The dataset is `cc0-1.0`. The addon packages under `packages/` are the work of their authors and stay under their
own licenses.
