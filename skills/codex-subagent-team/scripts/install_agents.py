#!/usr/bin/env python3
"""Install managed Codex agent profiles and register them in config.toml."""

from __future__ import annotations

import argparse
import os
import stat
import tempfile
import tomllib
from pathlib import Path


ROLES = ("luna_patcher", "sol_executor", "terra_executor", "terra_reviewer")
BEGIN_MARKER = "# BEGIN codex-subagent-team managed roles"
END_MARKER = "# END codex-subagent-team managed roles"


def strip_managed_block(text: str, config_path: Path) -> str:
    lines = text.splitlines(keepends=True)
    begins = [index for index, line in enumerate(lines) if line.rstrip("\r\n") == BEGIN_MARKER]
    ends = [index for index, line in enumerate(lines) if line.rstrip("\r\n") == END_MARKER]
    if len(begins) != len(ends) or len(begins) > 1:
        raise ValueError(f"Managed Subagent config markers are incomplete or duplicated: {config_path}")
    if not begins:
        return text
    if ends[0] < begins[0]:
        raise ValueError(f"Managed Subagent config markers are out of order: {config_path}")
    return "".join(lines[: begins[0]] + lines[ends[0] + 1 :])


def parse_config(text: str, config_path: Path) -> dict:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"Codex config.toml is invalid: {config_path}: {error}") from error


def toml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def managed_block(target_dir: Path) -> str:
    lines = [BEGIN_MARKER]
    for role in ROLES:
        lines.extend((f"[agents.{role}]", f'config_file = "{toml_string(str(target_dir / f"{role}.toml"))}"', ""))
    lines.append(END_MARKER)
    return "\n".join(lines) + "\n"


def atomic_write(path: Path, data: bytes, mode: int) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def install(codex_home: Path) -> None:
    script_dir = Path(__file__).resolve().parent
    source_dir = script_dir.parent / "assets" / "agents"
    target_dir = codex_home / "agents"
    config_path = codex_home / "config.toml"
    profiles = {path.stem: path for path in source_dir.glob("*.toml") if path.is_file()}
    if tuple(sorted(profiles)) != ROLES:
        raise ValueError(f"Expected managed Subagent profiles {ROLES}, found {tuple(sorted(profiles))}")
    if config_path.is_symlink():
        raise ValueError(f"Refusing to replace symlinked Codex config.toml: {config_path}")
    for role in ROLES:
        target = target_dir / f"{role}.toml"
        if target.is_symlink():
            raise ValueError(f"Refusing to replace symlinked Subagent profile: {target}")

    original = config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
    unmanaged = strip_managed_block(original, config_path)
    parsed = parse_config(unmanaged, config_path)
    agents = parsed.get("agents", {})
    if not isinstance(agents, dict):
        raise ValueError(f"Codex agents configuration is not a table: {config_path}")
    collisions = sorted(set(ROLES).intersection(agents))
    if collisions:
        raise ValueError(f"A managed Subagent role already exists outside the managed block: {config_path}: {', '.join(collisions)}")

    prefix = unmanaged.rstrip("\r\n")
    candidate = (prefix + "\n\n" if prefix else "") + managed_block(target_dir)
    parse_config(candidate, config_path)

    target_dir.mkdir(parents=True, exist_ok=True)
    for role in ROLES:
        source = profiles[role]
        target = target_dir / source.name
        data = source.read_bytes()
        if target.is_file() and not target.is_symlink() and target.read_bytes() == data:
            print(f"Unchanged Subagent: {role}")
        else:
            atomic_write(target, data, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            print(f"Installed Subagent: {role}")

    codex_home.mkdir(parents=True, exist_ok=True)
    atomic_write(config_path, candidate.encode("utf-8"), stat.S_IRUSR | stat.S_IWUSR)
    print(f"Installed {len(ROLES)} managed Subagents in {target_dir} and registered them in {config_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-home", required=True, type=Path)
    args = parser.parse_args()
    try:
        install(args.codex_home.expanduser().resolve())
    except (OSError, UnicodeError, ValueError) as error:
        print(str(error), file=os.sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
