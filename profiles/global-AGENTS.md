# Global Agent Working Agreement

## Before changing anything

- Start from the exact live repository, document, configuration, or artifact named by the user.
- Read applicable `AGENTS.md`, README, status documents, and `git status --short` before editing.
- State assumptions and the narrow task boundary. Ask only when an undiscoverable choice would materially change the result.
- Preserve pre-existing changes and treat untracked files as user-owned.

## Implementation

- Make the smallest change that satisfies the request. Do not add speculative features or refactor unrelated code.
- Match the existing style and architecture. Remove only orphaned code created by the current change.
- Prefer reversible operations. Resolve exact targets before deletion, replacement, installation, or publication.
- Never upload credentials, private user data, sessions, logs, caches, local authorization state, or machine-specific secrets.

## Verification

- Define a concrete success check before implementation and loop until it passes or a real blocker is identified.
- Distinguish documented claims, code inspection, fresh tests, and rendered or runtime evidence.
- Review diffs and run the narrowest relevant tests. Do not describe unverified work as complete.

## Git closeout

- Stage only task-owned files; never use a blind `git add .` in a mixed worktree.
- Commit verified durable changes with a focused message.
- Push only when the user requested publication or the repository's publication policy is already explicit.
- Report the final branch, commit, verification result, and any remaining unrelated changes.
