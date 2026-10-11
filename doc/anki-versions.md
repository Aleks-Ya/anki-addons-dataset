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
