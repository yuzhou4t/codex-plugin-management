#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SKILL_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
SOURCE_DIR="$SKILL_DIR/assets/agents"
CODEX_HOME_DIR=${CODEX_HOME:-"$HOME/.codex"}
TARGET_DIR="$CODEX_HOME_DIR/agents"
CONFIG_PATH="$CODEX_HOME_DIR/config.toml"
BEGIN_MARKER="# BEGIN codex-subagent-team managed roles"
END_MARKER="# END codex-subagent-team managed roles"

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

umask 077
config_temp="$CONFIG_PATH.codex-subagent-team.tmp.$$"
trap 'rm -f "$config_temp"' EXIT HUP INT TERM
begin_count=0
end_count=0
if [ -f "$CONFIG_PATH" ]; then
  begin_count=$(grep -Fxc "$BEGIN_MARKER" "$CONFIG_PATH" || true)
  end_count=$(grep -Fxc "$END_MARKER" "$CONFIG_PATH" || true)
fi
if [ "$begin_count" -ne "$end_count" ] || [ "$begin_count" -gt 1 ]; then
  echo "Managed Subagent config markers are incomplete or duplicated: $CONFIG_PATH" >&2
  exit 1
fi

if [ "$begin_count" -eq 1 ]; then
  awk -v begin="$BEGIN_MARKER" -v end="$END_MARKER" '
    $0 == begin { inside=1; seen=1; next }
    $0 == end { if (!inside) exit 42; inside=0; next }
    !inside { print }
    END { if (inside || !seen) exit 43 }
  ' "$CONFIG_PATH" > "$config_temp"
else
  if [ -f "$CONFIG_PATH" ]; then
    cp "$CONFIG_PATH" "$config_temp"
  else
    : > "$config_temp"
  fi
fi

if grep -Eq '^[[:space:]]*\[agents\.(sol_executor|terra_executor|terra_reviewer|luna_patcher)\][[:space:]]*(#.*)?$' "$config_temp"; then
  echo "A managed Subagent role already exists outside the managed block: $CONFIG_PATH" >&2
  exit 1
fi

if [ -s "$config_temp" ] && [ -n "$(tail -c 1 "$config_temp")" ]; then
  printf '\n' >> "$config_temp"
fi
printf '%s\n' "$BEGIN_MARKER" >> "$config_temp"
for source_path in "$SOURCE_DIR"/*.toml; do
  [ -f "$source_path" ] || continue
  role=$(basename "$source_path" .toml)
  target_path="$TARGET_DIR/$role.toml"
  escaped_path=$(printf '%s' "$target_path" | sed 's/\\/\\\\/g; s/"/\\"/g')
  printf '[agents.%s]\nconfig_file = "%s"\n\n' "$role" "$escaped_path" >> "$config_temp"
done
printf '%s\n' "$END_MARKER" >> "$config_temp"
mv "$config_temp" "$CONFIG_PATH"
chmod 0600 "$CONFIG_PATH"
trap - EXIT HUP INT TERM

echo "Installed $installed_count managed Subagents in $TARGET_DIR and registered them in $CONFIG_PATH"
