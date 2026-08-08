---
name: git-finish
description: Automatically close out a main implementation task with Git. Use whenever Codex created or modified durable files in a Git repository, including features, fixes, refactors, project milestones, and aggregated subagent work, even if the user did not mention Git or request a commit. Inspect scope, verify safety, create a focused local commit when changes are task-owned, or report an explicit safe terminal state.
---

# Git Finish

## Core Rule

Treat Git closeout as a mandatory final gate for the main implementation task, not as an optional user reminder. If the task changed durable files inside a Git repository and verification passed, inspect and commit task-owned changes before the final completion response.

Subagents do not commit by default. The main agent owns the consolidated task commit unless commit ownership was explicitly delegated.

## Safety Boundaries

- Preserve pre-existing user changes.
- Never stage secrets, caches, private drafts, unrelated files, or bulky generated artifacts by accident.
- Do not commit a failed or materially unverified implementation as successful work.
- Do not push unless the user requested it or the remote and visibility policy are explicit.
- Never use a blind `git add .` in a mixed or unreviewed worktree.

## Required Workflow

1. Locate and inspect the repository:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
git diff --stat
git diff --check
```

2. Classify every changed path.
   - Identify task-owned, pre-existing user, generated, secret, and unrelated changes.
   - Include task-owned changes produced by delegated subagents in the main task scope.

3. Confirm verification evidence.
   - Use fresh tests, build, lint, smoke checks, or artifact inspection appropriate to the change.
   - If verification failed, do not create a success commit merely to make the tree clean.

4. Stage only task-owned paths:

```bash
git add path/to/file
git diff --cached --stat
git diff --cached --check
```

Review the staged diff before committing. Use patch staging when task and unrelated edits share a file and can be separated safely; otherwise stop with a blocked state.

5. Create a focused local commit without waiting for another reminder:

```bash
git commit -m "Describe focused change"
```

6. Re-check the result:

```bash
git status --short
git log -1 --oneline
```

Remaining unrelated user changes are allowed only when they are identified explicitly in the final response.

## Required Terminal State

Return exactly one Git closeout state:

- `committed: <sha>` — task-owned verified changes were committed.
- `clean / no-op` — no durable task change exists or the task change was already committed.
- `not a Git repo` — tell the user and offer `git init` when appropriate.
- `blocked: <reason>` — committing is unsafe because ownership is unclear, unrelated changes cannot be separated, verification failed, secrets/generated artifacts are in scope, or the user said not to commit.

Do not silently skip Git closeout. Do not report a main implementation task fully complete without one of these states.
