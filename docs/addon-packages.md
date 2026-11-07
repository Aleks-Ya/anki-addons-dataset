# Addon packages
DOWNLOAD saves the `.ankiaddon` package of every addon branch. PARSE derives metadata and code size from them
(`AddonInfo.package`), and REPORT exports these as the `packages` table and the `package` field of the main table.

## What PARSE derives
`PackageEnricher` runs after `ForkResolver` and reads only `1-raw/5-package/`, so a changed `PackageAnalyzer` takes
effect by re-running PARSE. It keeps the newest `updated` per minimum point version, and a package that cannot be read
(not a zip, truncated, an unsupported compression method or encrypted files) gets a warning and no row. Any other
error stops PARSE, so a bug in the analyzer is not mistaken for broken packages. The AI step does not call it. An
addon or snapshot without packages gets `package=None`.

`PackageAnalyzer` reads the zip in memory, never extracts it and never executes anything:

- `__MACOSX/` and `._*` entries are skipped everywhere. They can end in `.py` but are not Python, and at least 10 of
  189 sampled packages contain them.
- `manifest.json` and `config.json` come only from the zip root, as raw text. `manifest.json` is absent from about
  half of the packages, and it often has fields `ManifestParser` drops (`version`, `author`).
- A manifest or config over 64 kB gives `null`. A file over 5 MB is not read: a `.py` file counts as a file with no
  lines, and no file gets a language. Both limits use the size declared in the zip.
- `language_bytes` sums the uncompressed size of the files of each language. The language is the label
  [Magika](https://github.com/google/magika) gives the file content, ignoring the extension, counted only when its
  group is `code` (so `json`, `html` and `css` count, `markdown`, `txt` and images do not). Magika needs at least 8
  bytes; shorter files get `txt`, so they are not counted.
- REPORT's `primary_language` is the first entry of `language_bytes` that is not a data or config format
  (`JsonAddonInfo.__data_languages`: `json`, `jsonl`, `csv`, `tsv`, `xml`, `yaml`, `ignorefile`, ...). Bundled word
  lists and dictionaries often outweigh the code, so without this `json` or `csv` would win for about 130 addons.

Magika takes a few milliseconds per file, and a snapshot holds about 500k files, so `PackageEnricher` analyzes
packages on one thread per CPU. One `PackageAnalyzer` serves the whole PARSE run and remembers each package by file
name (which holds its hash), so a package hardlinked into several snapshots is analyzed once.

## How AnkiWeb serves a package
This is the request Anki itself makes:

```
GET /shared/download/<addon id>?v=2.1&p=<point version>
303 /svc/shared/download-addon/<addon id>?t=<epoch>&minpt=<min>&maxpt=<max>&bidx=<branch index>
200 the zip
```

- `t` is the same for all branches of an addon, so updating one branch changes it for every branch. It cannot
  identify a branch's version. The newest branch's `updated` date on the addon page matched the date of `t` on
  all 45 checked addons whose page was current.
- `manifest.json` has a `mod` field in some packages, but it is set by the author (some say 1970) and
  often differs from the page date. It is not used.
- Branches can overlap. A page listing `2.1.24-2.1.36` and `2.1.36-2.1.38` gets the lower branch for `p=36`,
  so a branch whose `p=min` lands elsewhere is requested again with `p=max`.
- A package can be missing: one addon of 50 had a valid redirect and then a 404. It gets a warning and is
  retried on the next run, as is a package that fails with a request or file system error or an unexpected
  redirect. Any other error stops DOWNLOAD.
- The responses have no `ETag` or `Last-Modified`, so conditional requests are not possible.

## Layout
```
history/YYYY-MM-DD/1-raw/
    5-package/{addon-id}/{min point version}-{branch updated}-{sha256, first 12}.ankiaddon
    package-list.json
```

## Cache
`PackageCacheIndex` indexes the packages of all snapshots by addon id, minimum point version and the branch's
`updated` date, all three taken from the addon page already scraped. For each branch, `PackageCollector`:

1. Skips it if this snapshot already holds the key.
2. Otherwise, if an older snapshot holds the key and `updated` is earlier than that snapshot's date, hardlinks
   the file (or copies it, on another file system). No request reaches AnkiWeb. A branch updated on the day of
   the holding snapshot could have changed again after that snapshot ran, so it is downloaded again.
3. Otherwise downloads it to a `.part` file, checks it is a zip and renames it. If an identical file already
   exists in another snapshot, it is hardlinked instead.

An addon page with no branches has no key, so it asks AnkiWeb with the point version from the catalog header,
then with `p=0` (some of these addons return 404 for one of the two), and builds the key from the redirect's
`minpt` and the date of `t`. The package body is not read if that key is cached.

The cache trusts the page date: a package replaced without its branch's `updated` date changing would be missed.

## Publishing
Packages are already zips, and most stay unchanged between snapshots, so they are left out of `raw.zip`.

- **BUNDLE** hardlinks each distinct file into `bundle/packages/{addon-id}/`, and `raw.zip` holds only
  `package-list.json`, the list of the files that snapshot used.
- **UPLOAD** pushes `packages/` with the rest of the bundle. `packages` is not in `huggingface.synced_dirs`, so
  `prune_orphans` never deletes a remote package, even if a local file is lost. Old versions stay on HuggingFace
  unless removed by hand. The remote `.gitattributes` has a `*.ankiaddon` rule, so packages are stored in LFS.
- **INIT** downloads `packages/` once and links the listed files into each snapshot. Snapshots without a package
  list are skipped.

History cannot be backfilled: AnkiWeb serves only current packages.
