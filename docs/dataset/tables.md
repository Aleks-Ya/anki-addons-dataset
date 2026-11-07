# Other tables

The tables published beside the main table ([addon fields](addons.md)). Each is a HuggingFace config of the same
name. Back to the [dataset card](https://huggingface.co/datasets/Ya-Alex/anki-addons).

## tags
The vocabulary the AI picks `ai.tags` from, with the meaning of every tag: function tags (what an addon does) and
status tags (`obsolete`, `paid`, ...).

## anki_versions
The stable Anki releases from 2.1.0 on, newest first, taken from the tags of the
[Anki repository](https://github.com/ankitects/anki) (betas and release candidates left out).
- `point_version` is Anki's sortable integer encoding of a version (`2.1.66` → `66`, `25.09.2` → `250902`), the
  same as the addons' `*_point_version` fields.
- `release_date` is the GitHub release date (UTC): `null` for most versions before 2.1.22, and too late for 2.1.15
  and 2.1.20.

How addon version ranges are parsed: [anki-versions.md](../anki-versions.md).

## reviews
The user reviews from the AnkiWeb addon pages, one row per review: `addon_id`, `date`, `vote` (`like` or
`dislike`), `text` (empty for a review without text) and `author_reply` (or `null`). AnkiWeb does not show
reviewers, so there is no reviewer column. The `likes`/`dislikes` counts of the main table can differ slightly
from the votes of the listed reviews. Parquet only.

## packages
The `.ankiaddon` packages served by AnkiWeb, one row per addon branch; `file_name` is the file under
`packages/{addon_id}/` (see [files](files.md)). Parquet only.
- Languages are detected from file content by [Magika](https://github.com/google/magika) and named as on GitHub
  (`Python`, `C++`, `Assembly`), like `github.language_bytes`. Unlike GitHub, they include bundled libraries and
  data formats such as `JSON`.
- Counts include bundled libraries.
- `manifest_json` and `config_json` are `null` when absent or over 64 kB.

How packages are downloaded and analyzed: [addon-packages.md](../addon-packages.md).
