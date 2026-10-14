---
name: token-usage-inspector
description: Inspect current or historical Codex token usage from local rollout logs. Use for one task, every task in a project, all locally retained tasks, model/date/project breakdowns, legacy logs, CSV/JSON export, or a live local usage watch. Do not use to estimate usage for chats that have no local Codex rollout log.
---

# Token Usage Inspector

Read Codex's local `rollout-*.jsonl` logs without contacting a model or uploading conversation data. Exact-session views support both native per-call `token_usage_record` counters and `task_started` / `token_count` events. Historical views aggregate native calls or reconstruct increments from cumulative `token_count` snapshots, removing spawned-agent inherited replay.

## Resolve the task

Use the bundled `scripts/inspect_token_usage.py` relative to this file.

- If the user supplies a Codex task/thread ID, use `--thread-id ID`.
- If the user supplies a rollout file, use `--session PATH`.
- If the target is unclear, use `--list-sessions` and identify the intended local task by timestamp and ID. Add `--include-prompt` only when a prompt preview is necessary and safe to show; ordinary user messages are associated with the following `task_started` event when they do not carry an explicit turn ID.
- Use `--latest` only when the most recently modified local session is known to be the requested task. Concurrent tasks can make this ambiguous.

The script searches `${CODEX_HOME}/sessions` and `${CODEX_HOME}/archived_sessions` when `CODEX_HOME` is set, otherwise the corresponding paths under `~/.codex`. Use `--active-only` only when archived logs must be excluded. A deleted log, cloud-only task, or ChatGPT web/shared conversation may have no corresponding local record; report that boundary instead of estimating.

## Query usage

Prefer user-turn totals for ordinary questions:

```bash
python3 scripts/inspect_token_usage.py --thread-id TASK_ID --granularity turn
```

Use individual model-call records when explaining why one user turn accumulated many tokens:

```bash
python3 scripts/inspect_token_usage.py --thread-id TASK_ID --granularity call
```

For a live local snapshot that refreshes every two seconds:

```bash
python3 scripts/inspect_token_usage.py --thread-id TASK_ID --granularity turn --watch 2
```

On Windows, use `python` or `py -3` if `python3` is unavailable. CSV and JSON exports are supported with `--format csv|json --output PATH`.

## Query historical usage

List locally recorded project directories before choosing a scope:

```bash
python3 scripts/inspect_token_usage.py --list-projects --limit 100
```

Aggregate every retained task whose recorded working directory exactly matches a project:

```bash
python3 scripts/inspect_token_usage.py \
  --project /absolute/project/path \
  --from 2026-07-01 --to 2026-09-30 \
  --timezone Asia/Shanghai \
  --group-by month,model
```

`--to YYYY-MM-DD` includes that entire local calendar day. An ISO datetime passed to `--to` is an exclusive cutoff. Add `--include-subdirs` only when child working directories belong in the same project scope.

Aggregate every locally retained task, or inspect one task across all of its rollout files:

```bash
python3 scripts/inspect_token_usage.py --all-sessions --group-by project,model
python3 scripts/inspect_token_usage.py --thread-id TASK_ID --historical --group-by month,model
```

Valid grouping fields are `month`, `day`, `model`, `project`, `task`, and `source`. Repeat `--model` for exact model filters and `--exclude-thread` for tasks that must be omitted. Historical reports include `record_source=native`, `legacy`, or both so the evidence basis remains visible.

## Interpret correctly

- `input_tokens` is cumulative model input across all calls in the selected grouping.
- `cached_input_tokens` is a subset of input tokens, not an additional amount.
- `uncached_input_tokens` is calculated as input minus cached input.
- `reasoning_output_tokens` is reported separately for diagnosis but is already represented by Codex's recorded output/total accounting; do not add it to `total_tokens` again.
- A user turn can contain many model calls after tool results. Its cumulative total can exceed the per-call context window.
- Mark the active turn as provisional. Its counters continue to grow until the final answer is recorded.
- Historical coverage is limited to rollout logs still present locally. Report the selected path, date cutoff, timezone, archive policy, and any excluded task IDs with the result.
- New native call records and old cumulative snapshots are selected per rollout file. Do not add both sources from the same file.
- Spawned-agent snapshots recorded before `inter_agent_communication_metadata` are inherited parent context and are used only as a baseline, not counted as child usage.
- Token counters describe model processing, not necessarily invoice cost or account rate-limit consumption. Do not infer price without the applicable current billing contract.

## Privacy boundary

Do not copy, publish, or commit rollout logs. They can contain prompts, tool outputs, local paths, and other sensitive context. Default output omits prompt text. Share or save only the aggregate report the user requested.
