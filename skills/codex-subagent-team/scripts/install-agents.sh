#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SKILL_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
SOURCE_DIR="$SKILL_DIR/assets/agents"
CODEX_HOME_DIR=${CODEX_HOME:-"$HOME/.codex"}
TARGET_DIR="$CODEX_HOME_DIR/agents"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "Agent profile source directory is missing: $SOURCE_DIR" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"
installed_count=0
for source_path in "$SOURCE_DIR"/*.toml; do
  [ -f "$source_path" ] || continue
  target_path="$TARGET_DIR/$(basename "$source_path")"
  if [ -f "$target_path" ] && cmp -s "$source_path" "$target_path"; then
    echo "Unchanged Subagent: $(basename "$source_path" .toml)"
  else
    cp "$source_path" "$target_path"
    chmod 0644 "$target_path"
    echo "Installed Subagent: $(basename "$source_path" .toml)"
  fi
  installed_count=$((installed_count + 1))
done

if [ "$installed_count" -ne 4 ]; then
  echo "Expected 4 managed Subagent profiles, found $installed_count" >&2
  exit 1
fi

echo "Installed $installed_count managed Subagents in $TARGET_DIR"
