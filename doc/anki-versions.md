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
reading addon data, such as the MCP server. Columns: `version` (the tag name, e.g. `25.09.2`, `2.1.66`),
`point_version` (`AnkiVersionCodec.to_point`) and `release_date` (the UTC date of the GitHub release's
`published_at`, or null). Rows are newest first.

- **DOWNLOAD** makes two requests, each with the ETag reuse of the previous snapshot. It fetches every tag of
  `ankitects/anki` (`/repos/ankitects/anki/git/matching-refs/tags`, unpaginated) into
  `1-raw/2-github/ankitects/anki/tags.json` (`TagNamesRepoHandler`), and the first page of its releases
  (`/repos/ankitects/anki/releases?per_page=100`) into `releases.json` next to it (`ReleasesRepoHandler`).
- **REPORT** reads those raw files (`AnkiVersionsCollector.read`). The tags decide the rows: it keeps the stable
  releases from 2.1.0 on, so a tag must be `X.Y` or `X.Y.Z` (betas and release candidates are dropped), and a
  `2.x` tag must be `2.1.z` (2.0 and older are dropped). The releases only supply the dates, and their
  `prerelease` flag is ignored because it is unreliable (`26.09.1` is a stable version flagged as a prerelease).
  REPORT needs no GitHub token, and changing the filter needs only REPORT.
- A snapshot without `tags.json` (downloaded before the table existed) gets no `anki_versions` files;
  REPORT logs a warning. The rows of the history are not backfilled: the tag list carries no dates, so today's
  list would show releases that did not exist yet when an old snapshot was collected.
- A snapshot with `tags.json` but no `releases.json` gets the table with every `release_date` null; REPORT logs
  a warning.

**Limits of `release_date`:**
- Null for a stable tag with no GitHub release: 2.1.0-2.1.14, 2.1.16-2.1.19, 2.1.21 and 25.02.1-25.02.3.
- The releases of 2.1.15 and 2.1.20 were published late, both on 2020-03-07, while their tags are from
  2019-09-20 and 2020-02-13.
- Only the first page is fetched. Anki had 88 releases in October 2026, about 14 more a year, so past 100 the
  oldest releases fall off the page and their dates become null.

**Adding the table or the dates to an existing snapshot.** DOWNLOAD skips every raw file that already exists, so
re-running it on the snapshot's date fetches only what is missing:
```bash
uv run anki-addons-dataset download -d 2026-10-01   # only fetches the missing tags.json and releases.json
uv run anki-addons-dataset report -d 2026-10-01     # no parse needed
uv run anki-addons-dataset bundle upload
```
Use the same `--sample-addons` as the original download (none for a published snapshot): DOWNLOAD rewrites
`1-raw/sample.json`. Add a missing `tags.json` to the latest snapshot only, for the reason above. A missing
`releases.json` can be added to any snapshot that has `tags.json`: the rows still come from that snapshot's own
tags, so newer releases add no rows.
