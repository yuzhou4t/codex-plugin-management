---
name: aihot
description: Query the current AI HOT service for recent Chinese AI news, hot topics, daily reports, company or keyword updates, and category-specific items. Use when the user explicitly mentions AI HOT or asks for current AI-industry news such as 今天 AI 圈、最近 AI 新闻、当前热点、AI 日报、模型发布、产品发布或最近一周 AI 论文. Do not use for the local AI充电站 project or its latest-report/latest-workflow artifacts; use ai-charging-station-daily there.
---

# AI HOT

Use AI HOT as a live source. Do not answer current-news questions from model memory.

## Query

Set the installed skill directory once:

```bash
AIHOT_SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/aihot"
```

Use the bundled client rather than rebuilding URLs by hand:

```bash
node "$AIHOT_SKILL_DIR/scripts/fetch-aihot.mjs" items --window 24h --limit 50
```

Route by the user's wording:

| Intent | Command |
|---|---|
| 今天、过去 24 小时、最近有什么 | `items --window 24h` |
| 最近一周 | `items --window 7d` |
| 现在最热的事件 | `hot-topics` |
| 明确说“日报” | `daily` |
| 指定日期日报 | `daily --date YYYY-MM-DD` |
| 日报存档 | `dailies --limit N` |
| 明确要全部/完整/全量 | add `--mode all` |
| 模型、产品、行业、论文或技巧 | add `--category <slug>` |
| 公司、产品或主题 | add `--query "<keyword>"` |

Defaults are selected items, timeline ordering, a 24-hour window, and at most 50 results. Use `--by published` only when the user specifically wants the original publishers' timestamps instead of AI HOT's current timeline.

Current category slugs are `ai-models`, `ai-products`, `industry`, `paper`, and `tip`. Treat future string values as valid rather than failing.

For a durable local mirror, read the official OpenAPI and use the `snapshot` and `changes` commands. Do not use rolling-window pagination as an exact synchronization protocol.

## Verify Contract Drift

The stable contract is:

```text
https://aihot.virxact.com/openapi-v1.json
```

Read it when the service rejects a documented parameter, returns an unfamiliar schema, or the user asks about API integration. Do not use the legacy `/api/public/*` contract for new work.

The API is anonymous and read-only. A custom User-Agent is diagnostic metadata, not an access requirement. On HTTP 429 or 503, honor `Retry-After`; on other failures, report the returned request id when present and do not invent news.

## Present Results

Return a concise Chinese brief:

- State the human-readable time window and number of items.
- Group mixed results by category; use a flat list for a single category.
- For each item include the Chinese title, source name, readable Beijing time, short summary, and a clickable source link.
- Prefer `links.original` for provenance. Add `links.aihot` when the translated or normalized AI HOT page is useful.
- Explain why an item matters only when supported by the item, source, or explicit inference.
- If no items match, say so plainly. Do not pad the answer with older material.

Keep endpoint paths, raw parameters, cursors, cache headers, and rate-limit implementation details out of the reader-facing brief.

