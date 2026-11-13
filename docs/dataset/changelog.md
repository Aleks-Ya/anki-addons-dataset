# Changelog

The versions of the dataset, see [versioning.md](versioning.md).

## 1.1
ClamAV scan results of the addon packages: `clamav_signatures` and `clamav_database_version` in the `packages`
table, and `package.clamav_signatures` (of the newest branch) in `data`. `null` in snapshots that were not scanned.

## 1.0
The first versioned release: the schema in [schema.json](schema.json).

Tag `v1.0-2026-11-01` wrote the `tags` columns as `large_string` instead of the `string` that `schema.json`
records. Later tags match `schema.json` exactly.
