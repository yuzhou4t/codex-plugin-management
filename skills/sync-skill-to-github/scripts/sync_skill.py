#!/usr/bin/env python3
"""Preflight and copy one Skill into a Git-backed Skill repository."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import sys
import uuid


IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules"}
IGNORED_FILES = {".DS_Store", "Thumbs.db", "Desktop.ini"}
SENSITIVE_NAMES = {
    ".env",
    ".netrc",
    ".npmrc",
    "auth.json",
    "credentials.json",
    "cookies.json",
    "id_rsa",
    "state.sqlite",
    "session_index.jsonl",
}
SENSITIVE_SUFFIXES = {".db", ".gz", ".jsonl", ".key", ".log", ".p12", ".pem", ".pfx", ".sqlite", ".sqlite3", ".tar", ".tgz", ".zip", ".7z"}
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "GitHub token": re.compile(r"(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{30,})"),
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
}
MACHINE_PATH_PATTERNS = {
    "macOS home path": re.compile("/" + r"Users/[^/\s]+/"),
    "Linux home path": re.compile("/" + r"home/[^/\s]+/"),
    "Windows home path": re.compile(r"[A-Za-z]:\\" + r"Users\\[^\\\s]+\\"),
}
MAX_FILES = 500
MAX_BYTES = 25 * 1024 * 1024


class PreflightError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Skill directory containing SKILL.md")
    parser.add_argument("--repo", type=Path, required=True, help="Destination Git repository")
    parser.add_argument("--category", choices=("skills", "skills-macos"), default="skills")
    parser.add_argument("--origin", choices=("self", "external"), required=True)
    parser.add_argument("--source-url")
    parser.add_argument("--version")
    parser.add_argument("--license")
    parser.add_argument("--allow-machine-paths", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Copy after a successful preflight")
    return parser.parse_args()


def parse_skill_name(skill_file: Path) -> str:
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise PreflightError("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise PreflightError("SKILL.md frontmatter is not closed")
    match = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", text[4:end])
    if not match:
        raise PreflightError("SKILL.md must declare a lowercase hyphen-case name")
    return match.group(1)


def collect_files(source: Path) -> list[Path]:
    files: list[Path] = []
    total_bytes = 0
    for root, dirs, names in os.walk(source, followlinks=False):
        root_path = Path(root)
        for dirname in list(dirs):
            candidate = root_path / dirname
            if dirname in IGNORED_DIRS:
                dirs.remove(dirname)
            elif candidate.is_symlink():
                raise PreflightError(f"symlink directory is not allowed: {candidate}")
        for filename in names:
            path = root_path / filename
            if filename in IGNORED_FILES:
                continue
            if path.is_symlink():
                raise PreflightError(f"symlink file is not allowed: {path}")
            if filename in SENSITIVE_NAMES or filename.startswith(".env.") or path.suffix.lower() in SENSITIVE_SUFFIXES:
                raise PreflightError(f"sensitive file is not allowed: {path}")
            files.append(path)
            total_bytes += path.stat().st_size
            if len(files) > MAX_FILES:
                raise PreflightError(f"Skill exceeds the {MAX_FILES}-file limit")
            if total_bytes > MAX_BYTES:
                raise PreflightError(f"Skill exceeds the {MAX_BYTES // 1024 // 1024} MiB limit")
    return files


def scan_text(files: list[Path]) -> tuple[list[str], list[str]]:
    secrets: list[str] = []
    machine_paths: list[str] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                secrets.append(f"{label}: {path}")
        for label, pattern in MACHINE_PATH_PATTERNS.items():
            if pattern.search(text):
                machine_paths.append(f"{label}: {path}")
    return secrets, machine_paths


def validate_provenance(args: argparse.Namespace) -> None:
    if args.origin == "self":
        return
    if not args.source_url:
        raise PreflightError("external Skill requires an authoritative source_url")
    if not args.source_url.startswith("https://"):
        raise PreflightError("external source URL must use HTTPS")


def update_provenance(repo: Path, record: dict[str, str | None]) -> Path:
    manifest = repo / "manifests" / "synced-skills.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    skills = [item for item in data.get("skills", []) if item.get("name") != record["name"]]
    skills.append(record)
    data["skills"] = sorted(skills, key=lambda item: str(item["name"]))
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def update_external_link(repo: Path, record: dict[str, str | None]) -> Path:
    manifest = repo / "manifests" / "external-skills.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    linked = [item for item in data.get("linkedSkills", []) if item.get("name") != record["name"]]
    linked.append(record)
    data["linkedSkills"] = sorted(linked, key=lambda item: str(item["name"]))
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def copy_new_skill(source: Path, target: Path, files: list[Path]) -> None:
    if target.exists():
        raise PreflightError(f"destination already exists; review updates manually: {target}")
    temporary = target.parent / f".{target.name}.sync-{uuid.uuid4().hex}"
    temporary.mkdir(parents=False)
    try:
        for path in files:
            relative = path.relative_to(source)
            destination = temporary / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
        temporary.rename(target)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    repo = args.repo.expanduser().resolve()
    try:
        if not (repo / ".git").exists():
            raise PreflightError(f"destination is not a Git repository: {repo}")
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            raise PreflightError(f"source is not a Skill directory: {source}")
        skill_name = parse_skill_name(source / "SKILL.md")
        if source.name != skill_name:
            raise PreflightError(f"folder name '{source.name}' does not match Skill name '{skill_name}'")
        validate_provenance(args)
        files = collect_files(source)
        secrets, machine_paths = scan_text(files)
        if secrets:
            raise PreflightError("possible secrets detected:\n  " + "\n  ".join(secrets))
        if machine_paths and not args.allow_machine_paths:
            raise PreflightError("private absolute paths detected:\n  " + "\n  ".join(machine_paths))
        if args.allow_machine_paths and args.category != "skills-macos":
            raise PreflightError("--allow-machine-paths is only valid with --category skills-macos")

        target = repo / args.category / skill_name
        in_place = source == target.resolve() if target.exists() else False
        print(f"Skill: {skill_name}")
        print(f"Files: {len(files)}")
        print(f"Destination: {target}" if args.origin == "self" else "Destination: external link manifest only")
        print(f"Provenance: {args.origin}")
        if machine_paths:
            print(f"Machine paths explicitly allowed: {len(machine_paths)}")
        if not args.apply:
            action = "register the upstream link" if args.origin == "external" else "sync"
            print(f"Preflight passed; no files were written. Re-run with --apply to {action}.")
            return 0

        record = {
            "name": skill_name,
            "sourceUrl": args.source_url,
            "version": args.version,
            "license": args.license,
            "recordedAt": dt.datetime.now(dt.timezone.utc).date().isoformat(),
        }
        if args.origin == "external":
            manifest = update_external_link(repo, record)
            print("External link registered; third-party source was not copied.")
            print(f"External Skill manifest: {manifest}")
            return 0

        if not in_place:
            copy_new_skill(source, target, files)
        record.update({"category": args.category, "origin": args.origin})
        manifest = update_provenance(repo, record)
        print("Sync applied." if not in_place else "In-repository Skill audited.")
        print(f"Provenance manifest: {manifest}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, PreflightError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
