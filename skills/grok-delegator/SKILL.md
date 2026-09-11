---
name: grok-delegator
description: Delegate research, coding, frontend, or review work to a locally installed Grok CLI when the user explicitly says to use Grok, then verify scope and results in Codex. Use for requests such as 让 Grok 调研、调用 Grok 写代码、让 Grok 执行这个计划, or explicit $grok-delegator invocation; do not select Grok automatically for ordinary tasks.
---

# Grok Delegator

Use Grok only after the user explicitly requests it. The user's request authorizes sending the bounded task contract and the files needed for that task; it does not authorize unrelated private files, publishing, deployment, destructive cleanup, or account changes.

This Skill makes Codex the planner and acceptor. Grok is the bounded executor:

1. Inspect the current project, its instructions, Git state, and the files relevant to the request.
2. Write a concrete task contract. Show the user the concise goal, workspace, allowed edits, commands, checks, and acceptance criteria before transmission. If the user already asked to use Grok, continue without asking again unless the contract would expand the authorized data or side effects.
3. Run the bundled adapter and wait for its terminal receipt.
4. Inspect the actual diff and changed paths. Re-run or examine the independent checks, open real pages or apps for visual work, and open cited primary sources for research.
5. If acceptance finds a concrete defect, send one consolidated feedback file to the same Grok session with `resume`. Never silently start a replacement session.
6. Report what Grok actually did, what Codex independently verified, remaining limits, and whether anything was committed, pushed, deployed, or sent.

## Locate the adapter

On macOS or Linux:

```bash
GROK_DELEGATOR_DIR="${CODEX_HOME:-$HOME/.codex}/skills/grok-delegator"
python3 "$GROK_DELEGATOR_DIR/scripts/grok_delegate.py" doctor
```

On Windows PowerShell:

```powershell
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$GrokDelegatorDir = Join-Path $CodexHome "skills\grok-delegator"
python "$GrokDelegatorDir\scripts\grok_delegate.py" doctor
```

`doctor` discovers `grok` from `GROK_BIN`, `PATH`, or the user's standard Grok directory. It checks the installed CLI flags without reading or printing credentials. Do not hard-code a path copied from another computer.

If Codex's outer sandbox blocks Grok while Grok is preparing its own `workspace` sandbox, the error may mention writing `~/.grok/managed_config.toml`. Request access only for the Grok invocation or its own configuration directory, then rerun with Grok's `workspace` sandbox still enabled. Do not solve that error by turning Grok's sandbox off.

## Task contract

Read [references/task-contract.md](references/task-contract.md) when creating a task. Keep `cwd` as the smallest directory that contains the needed context. For focused tasks, declare writable files or directories in `allowed_paths`. When the user wants normal Codex-like project editing, set `workspace_write: true` so Grok can directly edit ordinary files throughout that task workspace while protected configuration and paths outside it remain denied. Declare every implementation command in `allowed_commands`; declare commands Codex must rerun in `checks`.

Use a temporary task and receipt path unless the user asks for a durable project record:

```bash
python3 "$GROK_DELEGATOR_DIR/scripts/grok_delegate.py" validate --task /absolute/path/task.json
python3 "$GROK_DELEGATOR_DIR/scripts/grok_delegate.py" run --task /absolute/path/task.json --receipt /absolute/path/receipt.json
```

The adapter uses Grok's `workspace` sandbox, disables Grok subagents and plan mode, removes API-key environment variables, and runs headlessly with project or focused file grants plus explicit command grants. It does not use `bypassPermissions` or `always-approve`. This matches Codex's project-level capability and approval boundary: ordinary task-workspace edits and task-authorized commands run directly; a protected path, external side effect, or host-level operation returns to Codex for review.

For a repair:

```bash
python3 "$GROK_DELEGATOR_DIR/scripts/grok_delegate.py" resume --receipt /absolute/path/receipt.json --feedback /absolute/path/feedback.txt
```

Stop after two evidence-based repair attempts with the same blocker. Do not change providers, loosen the sandbox, or add permissions merely to make the status green.

## Interpret receipts

- `needs_code_review`: Grok reached a terminal result, stayed in scope, and host checks passed. Codex must still review the diff and behavior.
- `needs_visual_review`: checks passed, but Codex must inspect the real interface and interactions.
- `needs_source_review`: Grok returned research with source URLs. Codex must open the important sources and assess claim support.
- `scope_violation`, `verification_failed`, `session_mismatch`, and `blocked_*`: not accepted.

Grok prose, exit code zero, or the presence of a file never completes acceptance by itself. Preserve unrelated dirty changes, and stage only task-owned files if the project requires a commit.

## Reusable prompts

Read [references/prompts.md](references/prompts.md) when the user asks for copyable setup text, a research prompt, or the Codex-plan/Grok-execute/Codex-accept workflow. The adapter already generates the executor prompt from the task contract; do not paste the long bootstrap prompt into every Grok call.
