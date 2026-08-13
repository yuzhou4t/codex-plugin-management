---
name: sync-skill-to-github
description: Safely audit, validate, commit, and push a newly created Skill to a configured GitHub Skill repository, while recording only the upstream link for third-party Skills. Use after creating, editing, downloading, or installing a Skill when the user wants it backed up, synchronized across computers, published to GitHub, or registered for later installation.
---

# Sync Skill to GitHub

Publish one Skill at a time. Treat the source Skill, unrelated repository changes, credentials, licenses, and machine-specific paths as separate safety boundaries.

## Required inputs

Resolve before writing:

- the exact source Skill directory containing `SKILL.md`;
- the exact destination Git repository, from the current repository or `CODEX_SKILL_REPO`;
- `skills/` for portable Skills or `skills-macos/` for explicitly machine-bound Skills;
- `self` or `external` provenance;
- for external Skills: the authoritative HTTPS download or repository URL; record a version and license when the upstream provides them.

Never copy third-party Skill source into this repository. Never guess an external license. Never hard-code a user's home directory into this Skill.

## Workflow

1. Read the destination repository's `AGENTS.md`, README, inventory, and Git status. Stop if pre-existing changes overlap the target Skill or inventory files.
2. Inspect only the source Skill directory. Do not execute downloaded scripts during review.
3. Run the bundled scanner without `--apply`:

```bash
python3 scripts/sync_skill.py /absolute/path/to/skill \
  --repo /absolute/path/to/codex-plugin-management \
  --category skills \
  --origin self
```

For an external Skill, supply its authoritative link. The script registers the link and does not copy the Skill:

```bash
python3 scripts/sync_skill.py /absolute/path/to/skill \
  --repo /absolute/path/to/codex-plugin-management \
  --category skills \
  --origin external \
  --source-url https://github.com/example/project \
  --version v1.2.3 \
  --license MIT
```

4. Resolve every reported secret, sensitive file, unknown license, symlink, excessive size, or private absolute path. Do not bypass a secret finding. Use `--allow-machine-paths` only for `skills-macos/` after the user explicitly accepts public path disclosure.
5. Repeat with `--apply`. For `self`, the script copies only a new Skill and refuses to overwrite an existing destination; review `manifests/synced-skills.json`. For `external`, it adds only the upstream link to `manifests/external-skills.json`.
6. Run the available Skill validator. Prefer the installed `skill-creator/scripts/quick_validate.py`; otherwise verify the YAML frontmatter, folder/name match, referenced resources, and UI metadata manually. Run bundled scripts only when they are trusted and required for validation.
7. Update `SKILL_INVENTORY.md`, README counts, and third-party notices when applicable. Run `python3 scripts/doctor.py --skip-plugins` and repository-specific tests.
8. Inspect `git diff`, `git diff --check`, and the remote URL. Stage only the copied Skill and its directly related manifest/documentation paths; never use `git add .` in a mixed tree.
9. Commit with a focused message and push the current branch. The request to use this Skill authorizes publishing the reviewed Skill, but not unrelated files. If the remote or visibility is unclear, credentials are detected, the branch is protected, or push would overwrite history, stop. Use a new `codex/` branch and open a pull request when direct push is unavailable.

## Hard stops

Do not publish:

- `.env`, authentication files, API keys, cookies, OAuth state, keychains, databases, logs, sessions, attachments, caches, or generated history;
- system-managed Skills or plugin caches as if they were user-maintained source;
- downloaded code without a traceable authoritative source;
- third-party source code that should be fetched from its upstream link instead;
- a Skill whose private paths or project data have not been deliberately classified;
- any unrelated dirty-worktree change.

## Completion report

Report the Skill name and destination, provenance, validation results, commit SHA, branch, GitHub URL, and any intentionally skipped local-only files.
