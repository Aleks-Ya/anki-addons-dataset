---
name: review-top-addons
description: Download the latest published anki-addons dataset from HuggingFace, take the top N highest-rated addons, cross-check every field (AnkiWeb links, GitHub, Anki Forum) against the live sources, and write a markdown report of discrepancies. Focuses especially on whether the GitHub repo and Anki Forum URL were correctly extracted from the addon page. Use when the user says "review top addons", "/review-top-addons", or asks to verify the top-rated addons' data for correctness.
allowed-tools: Bash(python3 *) Bash(gh api *) Bash(curl *) Bash(grep *) Bash(pip install *)
disable-model-invocation: true
---

# review-top-addons

Pull the latest published `Ya-Alex/anki-addons` dataset, take the top N highest-rated addons, verify each addon's fields against the live sources, and write a markdown report of the real discrepancies. The single most important check is whether the **GitHub repo and Anki Forum URL were extracted correctly from the addon page** — that is the most fragile part of the pipeline, and everything in the `github`/`forum` blocks is derived from it. Work through the steps in order; report clearly at the end.

`N` is the first argument the user gives (e.g. `/review-top-addons 20`). If none is given, **default to 10**.

## 1. Fetch the dataset and select the top N addons

```bash
python3 .claude/skills/review-top-addons/select_top_addons.py <N>   # N defaults to 10
```

This downloads `latest/parquet/data.parquet` (the canonical default config on HuggingFace) and `latest/metadata.json`, sorts by `anki_web.rating` descending, and writes to `~/anki-addons-dataset/reviews/`:

- `top-<N>-selected.json` — the selected records. Each record has `id`, `anki_web{title, addon_page_url, rating, update_date, anki_version, branches, links, likes, dislikes, ...}`, `github` (nullable), `forum` (nullable), **plus two derived helper fields** the script pre-extracts from the addon page HTML: `_page_github_urls` and `_page_forum_urls` (every `github.com` / `forums.ankiweb.net` URL actually present on the page).
- `pages/<id>.html` — the exact rendered page HTML the parser saw (the extraction ground truth).

Note the printed **snapshot date** — the dataset is a point-in-time snapshot, so counts will have drifted since then (see step 2). If the script fails because `huggingface_hub`/`pandas`/`pyarrow` are missing, `pip install huggingface_hub pandas pyarrow` and retry (or run `./pip_update.sh`). Read `top-<N>-selected.json` to drive the rest of the review.

## 2. Cross-check each addon against the live sources

For **each** selected addon, verify the fields below and record any mismatch. Do the link-extraction checks first — they are the priority.

### 2a. Link extraction (highest priority)

The addon page is client-side rendered, so it cannot be fetched with a plain GET — use the captured page instead. Ground truth = the page's own links, already extracted for you as `_page_github_urls` / `_page_forum_urls` (and the full HTML at `pages/<id>.html`, greppable with `grep -oE 'https?://github\.com/[^\"'\''<> )]+' ~/anki-addons-dataset/reviews/pages/<id>.html | sort -u`).

- **GitHub repo choice** — when `github` is non-null, confirm the chosen `github.user`/`github.repo` really is the addon's own repository and appears in `_page_github_urls`. Pages often link *several* repos (the author's other projects, contributors' forks, unrelated repos in prose); flag if the parser picked the wrong one, picked a fork/third-party repo over the author's, or invented a `user`/`repo` that appears nowhere on the page.
- **Missing GitHub** — when `github` is null but `_page_github_urls` clearly contains the addon's own repo, flag it as a missed extraction.
- **Forum URL** — when `forum` is non-null, confirm `forum.anki_forum_url` corresponds to a URL in `_page_forum_urls` and that `topic_slug`/`topic_id` match that URL. Pages may link multiple forum topics/categories; flag if the wrong topic was chosen, or if `forum` is null while an obvious official support thread is present in `_page_forum_urls`.

### 2b. GitHub enrichment (only if `github` is non-null)

Confirm the repo identity from 2a is right, then verify the enrichment values:

```bash
gh api repos/<user>/<repo> --jq '{full_name, stargazers_count, pushed_at, archived}'
gh api repos/<user>/<repo>/languages
```

- A **404** means the extracted repo URL is wrong — a genuine, high-value bug.
- Check `languages` matches `github.languages`, and `github.last_commit` is not *after* the repo's real last push (a `last_commit` in the future vs. reality is an error; the live repo being *newer* than the snapshot is just drift).
- `stars`, `action_count`, `tests_count`: sanity-check magnitude only (stars drift over time — see below).

### 2c. Forum enrichment (only if `forum` is non-null)

```bash
curl -s "https://forums.ankiweb.net/t/<topic_slug>/<topic_id>.json" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print({'id':d.get('id'),'slug':d.get('slug'),'posts_count':d.get('posts_count'),'last_posted_at':d.get('last_posted_at')})"
```

- A **404** / error means the extracted forum URL is wrong — a genuine bug.
- Confirm the returned `id`/`slug` match `forum.topic_id`/`forum.topic_slug`. Treat `posts_count`/`last_posted_at` as drift-prone (see below).

### Snapshot drift vs. real errors

The dataset is a snapshot as of the printed **snapshot date**. Values that naturally grow/advance over time — `rating`, `likes`, `dislikes`, `stars`, `posts_count`, `last_commit`, `last_posted_at` — will legitimately be *higher/later* live than in the dataset. **Only flag these when they moved impossibly** (live value *lower* than the snapshot by more than a rounding wobble, or a snapshot timestamp in the future relative to the live source). Always treat as **genuine issues**: wrong/misattributed GitHub repo or forum URL, 404 repo/topic, wrong/empty `title`, wrong `languages`, mismatched `anki_version`, malformed fields, or a `github`/`forum` block that is present but nonsensical.

Live re-verification of AnkiWeb scalar fields (`rating`, `likes`, `update_date`) is **limited**: the page is JS-rendered and can't be fetched directly, so verify those against the captured `pages/<id>.html` rather than a live GET, and note in the report that live AnkiWeb re-fetch was not performed.

## 3. Write the report

Write a markdown report to `~/anki-addons-dataset/reviews/top-<N>-review-<YYYY-MM-DD>.md` (use today's date):

- **Header** — N reviewed, snapshot date, review date, dataset file (`latest/parquet/data.parquet`).
- **Issues found** — a top-level summary listing only the real discrepancies, **link-extraction problems (wrong/missing/misattributed GitHub or forum URL) first and most prominently**, then other genuine errors. If there are none, say so explicitly.
- **Per-addon detail** — one section per addon (id, title, `addon_page_url`) with a compact table of the checked fields: dataset value vs. live/page value vs. verdict (✓ / ✗ / drift). Note where a live check couldn't be performed.

Then print a concise summary in chat: how many addons were reviewed, the count of real issues by type, and the full path to the report file. Lead with the link-extraction findings.

## Done

Report the outcome: number of addons reviewed, snapshot date, the list of genuine issues found (link-extraction problems first), and the path to the written report — or state clearly that all top-N addons checked out with no real discrepancies.
