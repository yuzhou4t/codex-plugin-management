---
name: journal-watch-paper-workflow
description: Operate the paper-processing and writing side of /Users/yuzhou4tc/Public/工作坊/journal-workshop-prototype. Use for a specific paper/job involving MinerU or DeepSeek nodes, editable preview, public-account drafting, Word export, issue export, abstract propagation, or workflow UI verification. Do not use for RSS discovery, journal adapters, source readiness, or the daily monitoring automation; those belong to science-workshop-journal-tracking.
---

# Journal Watch Paper Workflow

Work from `/Users/yuzhou4tc/Public/工作坊/journal-workshop-prototype`.

## Orient

Read the repository's `AGENTS.md`, `README.md`, relevant architecture/runbook/handoff document, and `git status --short`. Inspect the existing job folder, progress files, artifacts, and visible UI before restarting a run.

## Contracts

- Mark a node complete only when its output file or API response exists.
- Keep editable Markdown as the durable working format.
- Default draft surfaces to rendered preview with an explicit preview/edit toggle.
- Keep `nodes/final.md` as an editable local result.
- Export Word only on explicit user action; do not auto-create `exports/final.docx`.
- Preserve source facts and distinguish extraction defects from writing defects.
- Keep abstracts and keywords through extraction, frontend data, and UI display.
- Determine issue-export availability from issue metadata. Keep unavailable issues visible with a reason.
- For daily abstract backfill, target `data/push-history.json` rows by `first_seen_at`; do not rewrite `data/source-state.json`.

## Verify

Choose the narrowest check:

- backend or workflow logic: relevant backend tests
- UI structure: `scripts/workflow-ui-smoke-test.mjs`
- article artifacts: latest job files and API state
- frontend data: `data/push-history.json`, `data/recent-front-data.js`, and the latest workflow artifact
- backend health: `/api/health` on the documented local backend port

Report the inspected source/job id, node and artifact state, changed files, verification, and unresolved extraction, source, or network failures.

