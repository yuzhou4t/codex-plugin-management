---
name: science-workshop-journal-tracking
description: Maintain journal-source tracking for /Users/yuzhou4tc/Public/工作坊/journal-workshop-prototype. Use for RSS discovery, adapter profiles, source fallbacks, publication-date windows, recent article detection, source-state diagnosis, or the Science Workshop daily monitoring automation. Do not use for processing a selected paper through MinerU/DeepSeek, draft preview, Word export, or issue delivery; those belong to journal-watch-paper-workflow.
---

# Science Workshop Journal Tracking

Work from the live `journal-workshop-prototype` repository and read its instructions first.

## Inspect

Read only the surfaces relevant to the source problem:

- `data/adapter-profiles.json`
- extraction and adapter smoke scripts
- recent-window workflow scripts
- latest smoke results, recent article artifacts, source state, and frontend data

Classify failures before editing:

- DNS/network failure is an environment failure.
- 403, 412, WAF, login, CAPTCHA, or challenge pages are protection failures.
- Successful fetches with wrong items, dates, authors, or URLs are parser failures.
- Missing or inconsistent publication metadata is a data-quality problem.

Do not turn missing evidence into a code bug.

## Source Policy

- Prefer direct RSS/eTOC feeds, then public JSON or issue indexes, then metadata services such as Crossref or OpenAlex.
- Treat manual browsing as evidence for an automated rule, not the production path.
- Preserve `first_seen` behavior for sources without trustworthy dates.
- Mark a source ready only when smoke evidence contains usable samples or a documented fallback.

## Verify

Run the narrowest relevant checks; use the full sequence only for adapter changes:

```bash
node scripts/adapter-fallback-test.mjs
node scripts/recent-workflow-test.mjs
node scripts/adapter-smoke-test.mjs
node scripts/fetch-articles-smoke-test.mjs --workflow
node scripts/build-front-data.mjs
```

If the network is unavailable, run pure tests and inspect the latest successful artifacts. Report the limitation rather than marking all sources broken.

Reuse the existing `Science Workshop 每日文章检测` automation instead of creating a duplicate. Do not add GitHub pushing unless the user explicitly requests it.

