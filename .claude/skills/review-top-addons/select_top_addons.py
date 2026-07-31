#!/usr/bin/env python3
"""Download the latest published anki-addons dataset from HuggingFace and select
the top-N highest-rated addons for a correctness review.

Reads ``latest/parquet/data.parquet`` (the canonical default config declared by
the dataset card) with pandas, sorts by ``anki_web.rating`` descending, takes the
first N, and writes the selected records plus per-addon page HTML for
cross-checking. Also reports the snapshot's ``data_collection_date`` so the
reviewer can tell real errors apart from expected time-drift.

The AnkiWeb addon page is client-side rendered, so the *live* page can't be
fetched with a plain HTTP GET (WebFetch returns an empty shell). Instead the
dataset already stores the exact rendered HTML the parser saw in
``anki_web.addon_page_content`` — that HTML is the correct ground truth for
verifying that the GitHub repo and Anki Forum URL were extracted correctly. This
script saves that HTML per addon and pre-extracts the github.com / forum URLs it
contains, so the reviewer can compare them against the derived github/forum
blocks directly.

Usage:
    python3 select_top_addons.py [N]      # N defaults to 10

No auth required (the dataset is public).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd
from huggingface_hub import HfApi

REPO_ID = "Ya-Alex/anki-addons"  # mirrors HuggingFaceClient.__repo_id
DATA_FILE = "latest/parquet/data.parquet"
METADATA_FILE = "latest/metadata.json"
OUT_DIR = Path.home() / "anki-addons-dataset" / "reviews"

GITHUB_URL_RE = re.compile(r"https?://github\.com/[^\s\"'<>)]+", re.IGNORECASE)
FORUM_URL_RE = re.compile(r"https?://forums\.ankiweb\.net/[^\s\"'<>)]+", re.IGNORECASE)


def _to_plain(value):
    """Recursively convert numpy/pandas scalars and containers to plain JSON types."""
    if isinstance(value, dict):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain(v) for v in value]
    if hasattr(value, "tolist"):  # numpy array / scalar
        return _to_plain(value.tolist())
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _rating(record: dict) -> int:
    anki_web = record.get("anki_web") or {}
    try:
        return int(anki_web.get("rating") or 0)
    except (TypeError, ValueError):
        return 0


def _distinct(urls) -> list[str]:
    seen: dict[str, None] = {}
    for u in urls:
        u = u.rstrip(".,);]")  # strip trailing punctuation from prose links
        seen.setdefault(u, None)
    return list(seen)


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10

    api = HfApi()
    data_path = api.hf_hub_download(repo_id=REPO_ID, filename=DATA_FILE, repo_type="dataset")

    snapshot_date = "unknown"
    try:
        meta_path = api.hf_hub_download(repo_id=REPO_ID, filename=METADATA_FILE, repo_type="dataset")
        meta = json.loads(Path(meta_path).read_text())
        snapshot_date = meta.get("data_collection_date", "unknown")
    except Exception as exc:  # metadata is best-effort context, not essential
        print(f"WARNING: could not read {METADATA_FILE}: {exc}", file=sys.stderr)

    df = pd.read_parquet(data_path)
    records = [_to_plain(rec) for rec in df.to_dict(orient="records")]
    records.sort(key=_rating, reverse=True)
    top = records[:n]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pages_dir = OUT_DIR / "pages"
    pages_dir.mkdir(exist_ok=True)

    for rec in top:
        anki_web = rec.get("anki_web") or {}
        content = anki_web.pop("addon_page_content", None) or ""
        # Save the exact rendered page HTML the parser saw (extraction ground truth).
        (pages_dir / f"{rec.get('id')}.html").write_text(content, encoding="utf-8")
        # Pre-extract the links actually present in that HTML.
        rec["_page_github_urls"] = _distinct(GITHUB_URL_RE.findall(content))
        rec["_page_forum_urls"] = _distinct(FORUM_URL_RE.findall(content))

    out_file = OUT_DIR / f"top-{n}-selected.json"
    out_file.write_text(json.dumps(top, indent=2, ensure_ascii=False))

    print(f"Dataset repo : {REPO_ID}")
    print(f"Data file    : {DATA_FILE}")
    print(f"Snapshot date: {snapshot_date}")
    print(f"Total addons : {len(records)}")
    print(f"Selected     : {len(top)} (top-{n} by anki_web.rating)")
    print(f"Records JSON : {out_file}")
    print(f"Page HTML dir: {pages_dir}/<id>.html")
    print()
    header = f"{'rating':>6}  {'id':>11}  {'github (user/repo)':<38}  {'forum':<5}  title"
    print(header)
    print("-" * len(header))
    for rec in top:
        anki_web = rec.get("anki_web") or {}
        github = rec.get("github") or {}
        forum = rec.get("forum") or {}
        gh = f"{github.get('user')}/{github.get('repo')}" if github.get("user") else "-"
        has_forum = "yes" if forum.get("anki_forum_url") else "-"
        title = (anki_web.get("title") or "")[:55]
        print(f"{_rating(rec):>6}  {str(rec.get('id')):>11}  {gh:<38}  {has_forum:<5}  {title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
