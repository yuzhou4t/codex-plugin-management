---
name: new-project-loop
description: 项目从想法或现有代码改动到验证交付的大闭环。用于开新项目、实现功能、修复 Bug、重构、完成多步主任务、避免重复造轮子、选择 GitHub 先例、验证结果，以及在用户没有提醒时仍自动执行 Git 收尾并创建安全的任务级提交。
---

# Project Delivery Loop

Use this orchestration skill for new projects and existing-project implementation work. Keep details in the smaller skills it calls; use this skill to avoid missing discovery, implementation, verification, and Git closeout.

## The Main Loop

1. Define the intent.
   - Restate the requested outcome in one sentence.
   - Identify constraints and the done condition.
   - If the brief is fuzzy, proceed with explicit, low-risk assumptions or ask only when the choice materially changes the result.

2. Scout before substantial building.
   - Use `github-precedent-scout` when an existing repo, template, demo, library, or effect reference could save time.
   - Skip scouting for narrow fixes where the current repository already provides the relevant pattern.

3. Choose the smallest suitable route.
   - `reuse`: use an existing base.
   - `adapt`: customize a template or library.
   - `reference`: borrow a proven idea but build locally.
   - `from-scratch`: use only when reuse is not a good fit.

4. Orient and implement.
   - Use `project-orientation` for unfamiliar repositories.
   - Preserve user changes and make only task-scoped edits.
   - Treat subagent output as part of the main task; subagents should not create independent commits unless the main agent explicitly delegates commit ownership.

5. Verify the outcome.
   - Run the narrowest meaningful tests, build, smoke check, browser check, or artifact inspection.
   - Do not claim completion from code changes alone.
   - If verification fails or is blocked, report the exact blocker and do not create a success commit for unverified work.

6. Preserve knowledge when the milestone matters.
   - Use `neat-freak` when documentation, handoff material, or project rules need reconciliation.
   - Do not create documentation unless it reduces future context cost.

7. Run the mandatory main-task Git closeout gate.
   - Invoke `git-finish` after verification and immediately before the final completion response whenever the main task created or modified durable files in a Git repository.
   - Invoke it even when the user did not mention Git or ask for a commit.
   - Consolidate task-owned changes, including subagent changes, into one focused task or milestone commit when practical.
   - Do not let an implementation task end with an unexplained dirty worktree.
   - Push only when the user requested it or the remote and visibility policy are explicit.

## Required Git Terminal State

Before reporting an implementation task complete, report exactly one closeout state:

- `committed: <sha>` — verified task-owned changes were committed.
- `clean / no-op` — the task produced no durable Git changes or they were already committed.
- `not a Git repo` — report this plainly and offer initialization when appropriate.
- `blocked: <reason>` — committing would be unsafe because verification failed, unrelated changes are mixed in, ownership is unclear, secrets/generated artifacts are present, or the user explicitly prohibited a commit.

`blocked` is not a successful Git closeout. Preserve the files, state what remains uncommitted, and do not imply the task is fully closed.

## Output Shape

For completed implementation work, include:

- what changed
- what verification passed
- Git closeout state
- remaining risk or decision, if any
