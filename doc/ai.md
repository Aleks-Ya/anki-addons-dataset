# AI summaries and tags
The `ai` step generates the one-sentence addon summary exported as `ai.summary` and the addon tags
exported as `ai.tags`, picked from the vocabulary hard-coded in `AiTagger`. It is the only step
that spends money, so it is separate from `download`: it reads the snapshots already in `history/`,
builds a prompt from the addon title, the AnkiWeb description and the GitHub README, and
writes every answer to `history/<date>/1-raw/4-ai/ai-cache.jsonl`. `parse` then reads that cache
offline and attaches the summaries and tags to the dump; an addon with no cached answer simply gets
no summary or tags, and `parse` logs how many answers were missing (two per addon).
The step works on 50 addons at once, so up to 50 AI requests are in flight.

For an addon whose description or README links other catalog addons, a third request asks which one
of them, if any, the addon is a fork of. When that answer names a parent, the same prompt is asked
again of `ai.fork_verify_model` (`deepseek-v4-pro` by default), and the stronger model's answer is
final. Only a few hundred answers per snapshot name a parent, so this costs little. It is skipped when
the addon is a GitHub fork that already decides the parent, because `parse` then ignores the AI
answer. Set `fork_verify_model: false` to keep the first answer.

The cache key is a hash of the model and the whole prompt, system prompt included, so editing a
prompt template or `ai.readme_max_chars` invalidates every entry. Summaries and tags use different
prompts, so editing the tag vocabulary re-buys only the tag answers. That is why the step stands on its own — refilling
the cache costs AI tokens rather than a full re-scrape. The key holds no addon id or date, so an
unchanged prompt has the same key in every snapshot: the step loads a shared index from *all*
snapshots' caches and reuses any answer already bought anywhere in the history, copying each hit into
the current snapshot's cache file. A steady-state run only pays for addons whose text actually moved,
and re-running `ai` for an older snapshot, or reverting a prompt change, costs nothing.

`1-raw/` is bundled into `raw.zip` and published, so the cache is part of the public dataset. That is
what lets `init` restore it on a fresh machine. Each line holds the model, the answer and a SHA-256
of the prompt; the prompt text itself is not stored.

Without `-d` the step summarizes every snapshot, which is what a changed prompt needs; with `-d` it
summarizes that one snapshot only:

```bash
anki-addons-dataset ai                  # all snapshots; watch the per-snapshot hit/miss counts
anki-addons-dataset ai -d 2026-01-01    # one snapshot only
```

The date must name an existing snapshot, otherwise `ai` fails. Inside `all`, `-d` belongs to
`download` alone: the `ai` step of `all` keeps summarizing every snapshot. `parse` and `report` take
`-d` the same way, see [Running the pipeline](pipeline.md).

Against the default DeepSeek endpoint, `ai` refuses to run during DeepSeek's peak hours
(01:00-04:00 and 06:00-10:00 UTC, Monday through Friday), when the rate is double the off-peak
one, and fails with an error naming the window. Chinese public holidays are ignored: they only
turn peak hours into off-peak ones, so the check never lets a peak-rate request through.
