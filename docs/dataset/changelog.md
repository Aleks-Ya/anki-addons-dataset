# Changelog

The versions of the dataset, see [versioning.md](versioning.md).

## 1.1
ClamAV scan results of the addon packages: `clamav_signatures` and `clamav_database_version` in the `packages`
table, and `package.clamav_signatures` (of the newest branch) in `data`. `null` in snapshots that were not scanned.

The license found in the addon packages: `license`, `license_source` and `license_file` in the `packages` table, and
`package.license` and `package.license_source` (of the newest branch) in `data`.

One license per addon: `license.spdx_id` and `license.source` in `data`, from the package, the GitHub repo, the README
or the AnkiWeb description. `github.license` is now `NOASSERTION` instead of `null` when GitHub cannot identify the
repo's license file.

## 1.0
The first versioned release: the schema in [schema.json](schema.json).

Tag `v1.0-2026-11-01` wrote the `tags` columns as `large_string` instead of the `string` that `schema.json`
records. Later tags match `schema.json` exactly.
