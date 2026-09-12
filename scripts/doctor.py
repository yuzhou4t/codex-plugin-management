#!/usr/bin/env python3
"""Read-only portability audit for this Skill and plugin repository."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import os
import re
import shutil
import subprocess


PORTABLE_CONFIG_KEYS = ("model_reasoning_effort", "approval_policy", "sandbox_mode", "web_search")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home(), help="Home directory to inspect")
    parser.add_argument("--skip-plugins", action="store_true", help="Do not invoke the Codex CLI")
    parser.add_argument("--strict", action="store_true", help="Exit 2 when portable setup is incomplete")
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def skill_name(skill_file: Path) -> str | None:
    try:
        text = skill_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    match = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", text)
    return match.group(1) if match else None


def collect_repo_skills(repo: Path) -> tuple[list[str], list[str]]:
    names: list[str] = []
    errors: list[str] = []
    for category in ("skills", "skills-macos"):
        for directory in sorted((repo / category).iterdir()):
            if not directory.is_dir() or not (directory / "SKILL.md").is_file():
                continue
            declared = skill_name(directory / "SKILL.md")
            if declared != directory.name:
                errors.append(f"{category}/{directory.name}: frontmatter name is {declared!r}")
            names.append(directory.name)
    return names, errors


def assignment_keys(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    keys: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("["):
            break
        match = re.match(r"^([A-Za-z0-9_-]+)\s*=", line.strip())
        if match:
            keys.add(match.group(1))
    return keys


def flatten_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in flatten_strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in flatten_strings(child)]
    return []


def main() -> int:
    args = parse_args()
    repo = Path(__file__).resolve().parent.parent
    home = args.home.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []

    repo_skills, skill_errors = collect_repo_skills(repo)
    errors.extend(skill_errors)
    installed_dir = home / ".codex" / "skills"
    installed = {path.name for path in installed_dir.iterdir()} if installed_dir.is_dir() else set()
    missing_skills = sorted(set(repo_skills) - installed)
    if missing_skills:
        warnings.append(f"Codex Skills missing: {len(missing_skills)}")

    managed_agents_dir = repo / "skills" / "codex-subagent-team" / "assets" / "agents"
    managed_agents = sorted(managed_agents_dir.glob("*.toml")) if managed_agents_dir.is_dir() else []
    if len(managed_agents) != 4:
        errors.append(f"managed Subagent source count is {len(managed_agents)}, expected 4")
    installed_agents_dir = home / ".codex" / "agents"
    matching_agents = []
    for source in managed_agents:
        target = installed_agents_dir / source.name
        if not target.is_file():
            warnings.append(f"managed Subagent missing: {source.name}")
        elif sha256(source) != sha256(target):
            warnings.append(f"managed Subagent differs: {source.name}")
        else:
            matching_agents.append(source.name)

    profile = repo / "profiles" / "global-AGENTS.md"
    installed_profile = home / ".codex" / "AGENTS.md"
    if not installed_profile.is_file():
        warnings.append("global AGENTS.md is not installed")
    elif sha256(profile) != sha256(installed_profile):
        warnings.append("global AGENTS.md differs; review before replacing")

    config_keys = assignment_keys(home / ".codex" / "config.toml")
    missing_config = sorted(set(PORTABLE_CONFIG_KEYS) - config_keys)
    if missing_config:
        warnings.append("portable config keys missing: " + ", ".join(missing_config))

    external_manifest = json.loads((repo / "manifests" / "external-skills.json").read_text(encoding="utf-8"))
    expected_external = {
        name
        for group in external_manifest["groups"]
        for name in group["skills"]
    }
    agents_dir = home / ".agents" / "skills"
    installed_external = {path.name for path in agents_dir.iterdir()} if agents_dir.is_dir() else set()
    missing_external = sorted(expected_external - installed_external)
    if missing_external:
        warnings.append(f"external Skills missing: {len(missing_external)}")

    if not args.skip_plugins:
        manifest = json.loads((repo / "manifests" / "plugins.json").read_text(encoding="utf-8"))
        required = [item["id"] for item in manifest["repositoryPlugins"] if item.get("required")]
        codex = os.environ.get("PLUGIN_MANAGER_CODEX_BIN") or shutil.which("codex")
        if not codex:
            warnings.append("Codex CLI not found; plugin check skipped")
        else:
            try:
                result = subprocess.run(
                    [codex, "plugin", "list", "--json"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                if result.returncode:
                    warnings.append("Codex plugin list failed")
                else:
                    plugin_data = json.loads(result.stdout)
                    haystack = "\n".join(flatten_strings(plugin_data))
                    missing_plugins = [plugin for plugin in required if plugin not in haystack]
                    if missing_plugins:
                        warnings.append("repository plugins missing: " + ", ".join(missing_plugins))
            except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
                warnings.append("Codex plugin output could not be inspected")

    print(f"Repository Skills: {len(repo_skills)}")
    print(f"Installed repository Skills: {len(set(repo_skills) & installed)}")
    print(f"Installed managed Subagents: {len(matching_agents)}/{len(managed_agents)}")
    print(f"Installed external Skills: {len(expected_external & installed_external)}")
    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARN: {message}")
    if not errors and not warnings:
        print("OK: portable Codex setup matches the repository profile")
    if errors:
        return 1
    if warnings and args.strict:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
