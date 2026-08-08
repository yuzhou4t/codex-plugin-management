#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MARKETPLACE_DIR="$REPO_ROOT/marketplace"
SKILLS_SOURCE_DIR="$REPO_ROOT/skills"
CODEX_SKILLS_DIR="$HOME/.codex/skills"
PLUGINS=(build-web-apps test-android-apps zotero hyperframes)

if [[ -n "${PLUGIN_MANAGER_CODEX_BIN:-}" ]]; then
  CODEX_CLI="$PLUGIN_MANAGER_CODEX_BIN"
elif command -v codex >/dev/null 2>&1; then
  CODEX_CLI="$(command -v codex)"
elif [[ -x "/Applications/ChatGPT.app/Contents/Resources/codex" ]]; then
  CODEX_CLI="/Applications/ChatGPT.app/Contents/Resources/codex"
else
  echo "Codex CLI not found. Install Codex or set PLUGIN_MANAGER_CODEX_BIN." >&2
  exit 1
fi

if [[ ! -x "$CODEX_CLI" ]]; then
  echo "Codex CLI is not executable: $CODEX_CLI" >&2
  exit 1
fi

mkdir -p "$CODEX_SKILLS_DIR"
for skill_dir in "$SKILLS_SOURCE_DIR"/*; do
  [[ -d "$skill_dir" && -f "$skill_dir/SKILL.md" ]] || continue
  skill_name="$(basename "$skill_dir")"
  target_dir="$CODEX_SKILLS_DIR/$skill_name"
  mkdir -p "$target_dir"
  cp -R "$skill_dir"/. "$target_dir"/
  echo "Installed Skill: $skill_name"
done

"$CODEX_CLI" plugin marketplace add "$MARKETPLACE_DIR" --json
for plugin in "${PLUGINS[@]}"; do
  "$CODEX_CLI" plugin add "$plugin@plugin-management" --json
done

echo "Codex Skills and plugins installed from $REPO_ROOT"
