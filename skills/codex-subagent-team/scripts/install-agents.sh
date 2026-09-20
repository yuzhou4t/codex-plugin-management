#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CODEX_HOME_DIR=${CODEX_HOME:-"$HOME/.codex"}
PYTHON=${PYTHON:-python3}

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python 3.11 or newer is required to validate Codex config.toml safely." >&2
  exit 1
fi

exec "$PYTHON" "$SCRIPT_DIR/install_agents.py" --codex-home "$CODEX_HOME_DIR"
