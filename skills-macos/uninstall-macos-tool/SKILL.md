---
name: uninstall-macos-tool
description: Safely and completely uninstall a macOS app, CLI, SDK, developer tool, or desktop launcher. Use when the user says 卸载, 删除干净, 彻底删除, 移除软件, 清理相关文件, remove an app/CLI, or asks to remove the app bundle, user install directory, shell PATH block, package-manager entry, LaunchAgent, caches, preferences, logs, installer remnants, and command resolution together.
---

# Uninstall macOS Tool

Use an inventory -> scope confirmation -> removal -> fresh-environment verification workflow. Treat a complete uninstall as more than deleting one app bundle or binary.

## Safety Contract

- Start read-only. Identify the installation method and exact owned paths before deleting anything.
- For a broad or multi-path removal, show the exact deletion scope and obtain explicit confirmation before irreversible commands.
- Prefer the product's uninstaller or original package manager when available. Remove residual paths only after confirming ownership.
- Never remove a shared runtime, package-manager root, shell configuration file, or parent directory just because one target lives inside it.
- Avoid printing full shell-config diffs or environment dumps. Search for target-specific markers and redact credential-like values.
- Preserve unrelated files and processes. If ownership is ambiguous, stop and report the ambiguity.

## Workflow

1. Define the target.
   - Record the product name, expected command names, app/launcher names, and whether user data should also be removed.
   - Interpret `删除干净` as a request to inspect the full footprint, not as permission to guess unknown paths.

2. Inventory the footprint without changing state.
   - Check running processes and app bundles under `/Applications`, `~/Applications`, and the Desktop when a launcher may exist.
   - Resolve commands with `command -v` and inspect symlinks before removal.
   - Identify the installer: Homebrew, npm, pipx, Cargo, vendor installer, standalone directory, or copied app.
   - Search only relevant locations for target-named entries: user install directories, `~/Library/Application Support`, `Caches`, `Logs`, `Preferences`, `Saved Application State`, `LaunchAgents`, shell startup files, temporary build folders, installer archives, and installer-created backups.
   - Inspect shell startup files with target-specific `rg` patterns. Do not display unrelated lines.

3. Present the scope.
   - List exact paths grouped as app/launcher, executable/package, configuration/PATH, background service, cache/log, project or user data, and installer remnant.
   - Mark shared or uncertain items separately and exclude them from the deletion set.
   - State whether project files or user-created data are included. Wait for explicit confirmation when deletion is irreversible or the scope is broad.

4. Remove narrowly.
   - Quit the target app and stop only its identified background service.
   - Use the original uninstaller or package-manager uninstall command when it cleanly owns the installation.
   - Edit only the target-owned shell block or line; preserve the rest of the file byte-for-byte where practical.
   - Delete only the confirmed residual paths. Do not use broad wildcards or parent-directory deletion.

5. Verify from a fresh environment.
   - Confirm every approved path is absent.
   - Start a fresh login shell and verify each command no longer resolves, for example `/bin/zsh -lic 'command -v <command> || echo not-found'`.
   - Confirm target-specific shell markers, LaunchAgents, running processes, and app bundles are gone when applicable.
   - Report retained paths, failed removals, and any shared components intentionally left in place.

## Stop Conditions

- The target name matches multiple unrelated products.
- A candidate path contains user documents or project data that the user did not explicitly include.
- Removal would delete a shared runtime or another tool's package-manager files.
- The installation owner cannot be established safely.
- Verification reveals a still-running service or command from an unknown location; return to inventory instead of deleting more broadly.
