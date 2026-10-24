# Anki versions
The versions an addon supports are kept twice: the raw strings exactly as AnkiWeb shows them, and
parsed values following the rules of Anki itself (`int_version()`/`int_version_to_str()` in
`anki.utils`, `AddonMeta.compatible()` in `aqt/addons.py`). `AnkiVersionCodec` in
`common/anki_version.py` holds the parsing.

**Point version.** Anki encodes a version as one integer, which makes versions sortable (as strings,
`2.1.66` > `23.10`):

| Version | Point version | Rule |
| --- | --- | --- |
| `2.1.66` | `66` | `2.1.x` → `x` |
| `23.10` | `231000` | `YY.MM` → `YYMM00` |
| `25.09.2` | `250902` | `YY.MM.PP` → `YYMMPP` |
| `26.05b1` | `260500` | a beta/rc suffix decodes to its base release |

**Max version kind.** An addon's upper version has one of four meanings, exported as `max_version_kind`
(`anki_version_kind` for the addons list):

| Kind | Meaning | Anki's `max_point_version` |
| --- | --- | --- |
| `hard` | Anki disables the addon on any newer version | negative, `-B` |
| `tested` | the author tested up to this version; newer ones still run it | positive, `B` |
| `open` | no upper limit | — |
| `unknown` | the author gave no upper version | `0` |

**Where the values come from:**

| Source | Raw text | Parsed |
| --- | --- | --- |
| addon page, branch | `A-B+` | min `A`, max `B`, `tested` |
| | `A-B` | min `A`, max `B`, `hard` |
| | `A+` | min `A`, no max, `open` |
| | `A` | min `A`, no max, `unknown` |
| addons list, "Versions" column (the newest branch) | `B~` | `B`, `tested` |
| | `<=B` | `B`, `hard` |
| | empty | no version, `unknown` |
| GitHub `manifest.json` | `max_point_version: -B` | `B`, `hard` |
| | `max_point_version: B` | `B`, `tested` |
| | `max_point_version: 0` or absent | no version, `unknown` |

Exported fields, next to the unchanged raw ones:
- `anki_web`: `anki_point_version`, `anki_version_kind`
- `anki_web.branches[]`: `min_point_version`, `max_point_version`, `max_version_kind`
- `github.manifest`: `min_version`, `max_version`, `max_version_kind` (the raw point versions are converted
  back to version strings, `min_point_version`/`max_point_version` keep the integers as written)

An addons-list value that fits none of the forms is logged as a warning and becomes `unknown`; it never
fails the parse. Manifest values are copied as the author wrote them and are often odd (`260000` gives
"26.00"), so the AnkiWeb branches are the more reliable source. A dump written before these fields existed
still loads, with the parsed values empty and `unknown`; re-run `parse` to fill them.

## The `anki_versions` table
Every snapshot publishes the stable Anki releases as `anki_versions.{parquet,xlsx}` in `3-final/`
(published as the `anki_versions` HF config), for consumers that need the list of Anki versions without
reading addon data, such as the MCP server. Columns: `version` (the tag name, e.g. `25.09.2`, `2.1.66`) and
`point_version` (`AnkiVersionCodec.to_point`). Rows are newest first.

- **DOWNLOAD** fetches every tag of `ankitects/anki` with one request
  (`/repos/ankitects/anki/git/matching-refs/tags`, unpaginated) into
  `1-raw/2-github/ankitects/anki/tags.json` (`TagNamesRepoHandler`, so the ETag reuse of the previous
  snapshot applies).
- **REPORT** reads that raw file (`AnkiVersionsCollector.read`) and keeps the stable releases from 2.1.0 on:
  a tag must be `X.Y` or `X.Y.Z` (betas and release candidates are dropped), and a `2.x` tag must be `2.1.z`
  (2.0 and older are dropped). REPORT needs no GitHub token, and changing the filter needs only REPORT.
- A snapshot without the raw file (downloaded before the table existed) gets no `anki_versions` files;
  REPORT logs a warning. The history is not backfilled: the tag list carries no dates, so today's list
  would show releases that did not exist yet when an old snapshot was collected.

**Adding the table to an existing snapshot.** DOWNLOAD skips every raw file that already exists, so re-running
it on the snapshot's date fetches only the missing tag list:
```bash
uv run anki-addons-dataset download -d 2026-10-01   # only fetches 1-raw/2-github/ankitects/anki/tags.json
uv run anki-addons-dataset report -d 2026-10-01     # no parse needed
uv run anki-addons-dataset bundle upload
```
Use the same `--sample-addons` as the original download (none for a published snapshot): DOWNLOAD rewrites
`1-raw/sample.json`. Do this for the latest snapshot only, for the reason above.
