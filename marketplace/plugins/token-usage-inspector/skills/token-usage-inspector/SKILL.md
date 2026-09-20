---
name: token-usage-inspector
description: Inspect native Codex token usage for a current or previous local task, grouped by user turn or individual model call. Use when the user asks how many tokens a Codex conversation consumed, wants input/cache/output/reasoning details, needs CSV or JSON export, or wants a live local usage watch. Do not use to estimate token usage for ChatGPT web/shared chats that have no local Codex rollout log.
---

# Token Usage Inspector

Read the native token counters that Codex writes to local `rollout-*.jsonl` session logs. Current logs use `event_msg` records with `task_started`, `token_count`, `task_complete`, and `turn_aborted` payloads; older `token_usage_record` entries remain supported. The bundled script only aggregates those native counters; it does not tokenize text, contact a model, or upload conversation data.

## Resolve the task

Use the bundled `scripts/inspect_token_usage.py` relative to this file.

- If the user supplies a Codex task/thread ID, use `--thread-id ID`.
- If the user supplies a rollout file, use `--session PATH`.
- If the target is unclear, use `--list-sessions` and identify the intended local task by timestamp and ID. Add `--include-prompt` only when a prompt preview is necessary and safe to show; ordinary user messages are associated with the following `task_started` event when they do not carry an explicit turn ID.
- Use `--latest` only when the most recently modified local session is known to be the requested task. Concurrent tasks can make this ambiguous.

The script searches `${CODEX_HOME}/sessions` when `CODEX_HOME` is set, otherwise `~/.codex/sessions`. A cloud task or ChatGPT web/shared conversation may have no corresponding local rollout log; report that boundary instead of estimating.

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

## Interpret correctly

- `input_tokens` is cumulative model input across all calls in the selected grouping.
- `cached_input_tokens` is a subset of input tokens, not an additional amount.
- `uncached_input_tokens` is calculated as input minus cached input.
- `reasoning_output_tokens` is reported separately for diagnosis but is already represented by Codex's recorded output/total accounting; do not add it to `total_tokens` again.
- A user turn can contain many model calls after tool results. Its cumulative total can exceed the per-call context window.
- Mark the active turn as provisional. Its counters continue to grow until the final answer is recorded.
- Token counters describe model processing, not necessarily invoice cost or account rate-limit consumption. Do not infer price without the applicable current billing contract.

## Privacy boundary

Do not copy, publish, or commit rollout logs. They can contain prompts, tool outputs, local paths, and other sensitive context. Default output omits prompt text. Share or save only the aggregate report the user requested.
