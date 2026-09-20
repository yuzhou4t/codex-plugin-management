#!/usr/bin/env python3
"""Run a bounded Grok task and emit a receipt for independent Codex review."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
from typing import Any


MODES = {"research", "engineering", "frontend", "review"}
PROTECTED_PARTS = {".git", ".codex", ".agents", ".grok", ".env"}
IGNORED_DIRS = {".git", ".grok-delegator", "node_modules", ".venv", "__pycache__"}
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
URL_PATTERN = re.compile(r"https?://[^\s<>\"'\])}]+")
MAX_CAPTURE_BYTES = 12 * 1024 * 1024
MAX_SNAPSHOT_FILES = 50_000
MAX_HASH_BYTES = 16 * 1024 * 1024
REQUIRED_GROK_FLAGS = (
    "--prompt-file",
    "--cwd",
    "--output-format",
    "--no-subagents",
    "--no-plan",
    "--max-turns",
    "--sandbox",
    "--permission-mode",
    "--resume",
    "--model",
    "--reasoning-effort",
    "--tools",
    "--disable-web-search",
    "--disallowed-tools",
    "--allow",
    "--deny",
)


class ContractError(ValueError):
    pass


def emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def save_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        temporary.chmod(0o600)
    except OSError:
        pass
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot_read_json: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("JSON root must be an object")
    return value


def inside(root: Path, target: Path) -> bool:
    try:
        target.relative_to(root)
        return True
    except ValueError:
        return False


def normalize_path(root: Path, raw: str) -> tuple[str, Path]:
    if not isinstance(raw, str) or not raw.strip():
        raise ContractError("allowed_paths entries must be non-empty strings")
    candidate = Path(raw)
    if candidate.is_absolute() or candidate == Path(".") or ".." in candidate.parts:
        raise ContractError(f"unsafe allowed path: {raw}")
    if any(part in PROTECTED_PARTS or part.startswith(".env.") for part in candidate.parts):
        raise ContractError(f"protected allowed path: {raw}")
    absolute = (root / candidate).resolve(strict=False)
    if not inside(root, absolute):
        raise ContractError(f"allowed path escapes workspace: {raw}")
    normalized = candidate.as_posix().rstrip("/")
    return normalized, absolute


def normalize_command(value: Any, label: str) -> dict[str, Any]:
    if isinstance(value, list):
        argv = value
        timeout = 120
    elif isinstance(value, dict):
        argv = value.get("argv")
        timeout = value.get("timeout_seconds", 120)
    else:
        raise ContractError(f"{label} entries must be argv arrays or objects")
    if not isinstance(argv, list) or not argv or not all(isinstance(part, str) and part for part in argv):
        raise ContractError(f"{label} argv must be a non-empty string array")
    if not isinstance(timeout, int) or not 1 <= timeout <= 1800:
        raise ContractError(f"{label} timeout_seconds must be 1..1800")
    return {"argv": argv, "timeout_seconds": timeout}


def normalize_task(raw: dict[str, Any], source: Path) -> dict[str, Any]:
    task_id = raw.get("id")
    if not isinstance(task_id, str) or not ID_PATTERN.fullmatch(task_id):
        raise ContractError("id must match [A-Za-z0-9][A-Za-z0-9_-]{0,79}")
    mode = raw.get("mode")
    if mode not in MODES:
        raise ContractError(f"mode must be one of: {', '.join(sorted(MODES))}")
    goal = raw.get("goal")
    if not isinstance(goal, str) or not goal.strip():
        raise ContractError("goal must be a non-empty string")
    cwd_value = raw.get("cwd")
    if not isinstance(cwd_value, str) or not cwd_value.strip():
        raise ContractError("cwd must be a non-empty string")
    cwd_input = Path(cwd_value).expanduser()
    cwd = (source.parent / cwd_input).resolve() if not cwd_input.is_absolute() else cwd_input.resolve()
    if not cwd.is_dir():
        raise ContractError(f"cwd is not a directory: {cwd}")

    paths_value = raw.get("allowed_paths", [])
    if not isinstance(paths_value, list):
        raise ContractError("allowed_paths must be an array")
    allowed_paths: list[str] = []
    allowed_absolute: list[str] = []
    for item in paths_value:
        normalized, absolute = normalize_path(cwd, item)
        if normalized not in allowed_paths:
            allowed_paths.append(normalized)
            allowed_absolute.append(str(absolute))
    workspace_write = raw.get("workspace_write", False)
    if not isinstance(workspace_write, bool):
        raise ContractError("workspace_write must be true or false")
    if mode in {"engineering", "frontend"} and not allowed_paths and not workspace_write:
        raise ContractError(f"{mode} tasks require allowed paths or workspace_write=true")

    allowed_commands_value = raw.get("allowed_commands", [])
    checks_value = raw.get("checks", [])
    if not isinstance(allowed_commands_value, list) or not isinstance(checks_value, list):
        raise ContractError("allowed_commands and checks must be arrays")
    allowed_commands = [normalize_command(value, "allowed_commands") for value in allowed_commands_value]
    checks = [normalize_command(value, "checks") for value in checks_value]
    if mode in {"engineering", "frontend"} and not checks:
        raise ContractError(f"{mode} tasks require at least one independent check")

    acceptance_value = raw.get("acceptance", [])
    if isinstance(acceptance_value, str):
        acceptance = [acceptance_value]
    elif isinstance(acceptance_value, list) and all(isinstance(item, str) for item in acceptance_value):
        acceptance = acceptance_value
    else:
        raise ContractError("acceptance must be a string or string array")
    if not any(item.strip() for item in acceptance):
        raise ContractError("acceptance must include an observable criterion")

    timeout = raw.get("timeout_seconds", 1800)
    max_turns = raw.get("max_turns", 40)
    if not isinstance(timeout, int) or not 30 <= timeout <= 3600:
        raise ContractError("timeout_seconds must be 30..3600")
    if not isinstance(max_turns, int) or not 1 <= max_turns <= 80:
        raise ContractError("max_turns must be 1..80")
    web = raw.get("web", mode == "research")
    if not isinstance(web, bool):
        raise ContractError("web must be true or false")
    model = raw.get("model")
    effort = raw.get("reasoning_effort")
    if model is not None and (not isinstance(model, str) or not model.strip()):
        raise ContractError("model must be null or a non-empty string")
    if effort is not None and (not isinstance(effort, str) or not effort.strip()):
        raise ContractError("reasoning_effort must be null or a non-empty string")

    return {
        "id": task_id,
        "mode": mode,
        "cwd": str(cwd),
        "goal": goal.strip(),
        "allowed_paths": allowed_paths,
        "allowed_absolute_paths": allowed_absolute,
        "workspace_write": workspace_write,
        "allowed_commands": allowed_commands,
        "checks": checks,
        "acceptance": [item.strip() for item in acceptance if item.strip()],
        "web": web,
        "model": model,
        "reasoning_effort": effort,
        "timeout_seconds": timeout,
        "max_turns": max_turns,
    }


def find_grok(explicit: str | None = None) -> Path:
    candidates: list[str] = []
    if explicit:
        candidates.append(explicit)
    if os.environ.get("GROK_BIN"):
        candidates.append(os.environ["GROK_BIN"])
    discovered = shutil.which("grok")
    if discovered:
        candidates.append(discovered)
    home = Path.home()
    candidates.extend(
        str(path)
        for path in (
            home / ".grok" / "bin" / "grok",
            home / ".grok" / "bin" / "grok.exe",
            home / ".local" / "bin" / "grok",
        )
    )
    for value in candidates:
        path = Path(value).expanduser()
        if path.is_file() and (os.name == "nt" or os.access(path, os.X_OK)):
            return path.resolve()
    raise ContractError("grok CLI not found; set GROK_BIN or add grok to PATH")


def clean_environment() -> dict[str, str]:
    allowed = {
        "HOME",
        "PATH",
        "USER",
        "LOGNAME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TERM",
        "TMPDIR",
        "TMP",
        "TEMP",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "PROGRAMDATA",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "PATHEXT",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "GROK_HOME",
    }
    environment = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    environment["NO_COLOR"] = "1"
    environment["CI"] = "1"
    return environment


def command_text(argv: list[str]) -> str:
    return subprocess.list2cmdline(argv) if os.name == "nt" else shlex.join(argv)


def permission_path(path_value: str) -> str:
    path = Path(path_value)
    return str(path / "**") if path.is_dir() else str(path)


def executor_prompt(task: dict[str, Any], feedback: str | None = None) -> str:
    if task["workspace_write"]:
        allowed = "- all normal files under the task workspace\n- protected exclusions: .git, .codex, .agents, .grok, .env, and .env.*"
    else:
        allowed = "\n".join(f"- {path}" for path in task["allowed_paths"]) or "- none; return response text only"
    implementation_commands = task["allowed_commands"] + [
        check for check in task["checks"] if check not in task["allowed_commands"]
    ]
    commands = "\n".join(f"- {command_text(item['argv'])}" for item in implementation_commands) or "- none"
    acceptance = "\n".join(f"- {item}" for item in task["acceptance"])
    mode_note = {
        "research": "Use current web sources when web tools are enabled. Open original sources, cite direct URLs, include dates and evidence limits, and write the requested deliverable before returning.",
        "engineering": "Implement the complete bounded change, run the declared commands, repair failures, and leave the workspace ready for the host checks.",
        "frontend": "Implement the complete bounded interface change. The host will independently inspect the real page or app after checks pass.",
        "review": "Perform a read-only review and return evidence-based findings. Do not edit files unless an allowed path is explicitly declared.",
    }[task["mode"]]
    repair = f"\nAcceptance feedback from Codex:\n{feedback.strip()}\nFix every supported finding in this same session." if feedback else ""
    return f"""Codex has completed the plan and task contract. You are the sole Grok executor for this bounded task. Do not delegate or redesign the assignment.

Mode: {task['mode']}
Goal: {task['goal']}
Workspace: {task['cwd']}

Allowed edits only:
{allowed}

Commands you may run:
{commands}

Acceptance criteria:
{acceptance}

{mode_note}

Read the relevant workspace files, complete the whole task, run the declared checks available to you, repair failures, and return a concise account of actual changes, commands, sources, and remaining blockers. Preserve unrelated existing changes. Do not change permissions, account settings, Grok/Codex configuration, credentials, Git history, or the adapter. Do not commit, push, deploy, publish, send messages, install undeclared dependencies, or access unrelated private material. Do not claim a check passed unless it ran successfully. If a required permission or command is absent, stop and report the exact blocker instead of searching for a bypass.{repair}"""


def invocation(task: dict[str, Any], grok: Path, prompt_file: Path, session_id: str | None) -> list[str]:
    arguments = [
        str(grok),
        "--prompt-file",
        str(prompt_file),
        "--cwd",
        task["cwd"],
        "--output-format",
        "streaming-json",
        "--no-subagents",
        "--no-plan",
        "--max-turns",
        str(task["max_turns"]),
        "--sandbox",
        "workspace",
        "--permission-mode",
        "dontAsk",
    ]
    if session_id:
        arguments.extend(["--resume", session_id])
    else:
        if task["model"]:
            arguments.extend(["--model", task["model"]])
        if task["reasoning_effort"]:
            arguments.extend(["--reasoning-effort", task["reasoning_effort"]])

    tools = ["read_file", "grep", "list_dir"]
    if task["allowed_paths"] or task["workspace_write"]:
        tools.extend(["search_replace", "write"])
    if task["mode"] in {"engineering", "frontend"}:
        tools.append("run_terminal_command")
    if task["web"]:
        tools.extend(["web_search", "web_fetch"])
    arguments.extend(["--tools", ",".join(tools)])
    if not task["web"]:
        arguments.append("--disable-web-search")
    arguments.extend(
        [
            "--disallowed-tools",
            "scheduler_create,scheduler_delete,scheduler_list,monitor,image_gen,image_edit,image_to_video,reference_to_video,workflow",
            "--deny",
            "MCPTool(*)",
            "--allow",
            "Read",
            "--allow",
            "Grep",
        ]
    )
    if task["web"]:
        arguments.extend(["--allow", "WebFetch"])
    if task["workspace_write"]:
        workspace_pattern = str(Path(task["cwd"]) / "**")
        arguments.extend(["--allow", f"Edit({workspace_pattern})", "--allow", f"Write({workspace_pattern})"])
        for protected in (".git", ".codex", ".agents", ".grok", ".env", ".env.*"):
            protected_pattern = str(Path(task["cwd"]) / protected)
            if protected not in {".env", ".env.*"}:
                protected_pattern = str(Path(protected_pattern) / "**")
            arguments.extend(["--deny", f"Edit({protected_pattern})", "--deny", f"Write({protected_pattern})"])
    for raw in task["allowed_absolute_paths"]:
        pattern = permission_path(raw)
        arguments.extend(["--allow", f"Edit({pattern})", "--allow", f"Write({pattern})"])
    unique_commands: list[list[str]] = []
    for item in task["allowed_commands"] + task["checks"]:
        if item["argv"] not in unique_commands:
            unique_commands.append(item["argv"])
    for argv in unique_commands:
        text = command_text(argv)
        arguments.extend(["--allow", f"Bash({text})"])
    for text in ("git diff --check", "git status --short", "git diff -- .", "git log -5 --oneline"):
        arguments.extend(["--allow", f"Bash({text})"])
    return arguments


def file_fingerprint(path: Path) -> str:
    stat = path.lstat()
    if path.is_symlink():
        return "symlink:" + os.readlink(path)
    if stat.st_size > MAX_HASH_BYTES:
        return f"large:{stat.st_size}:{stat.st_mtime_ns}"
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for directory, names, files in os.walk(root, followlinks=False):
        names[:] = [name for name in names if name not in IGNORED_DIRS]
        base = Path(directory)
        for name in files:
            path = base / name
            relative = path.relative_to(root).as_posix()
            try:
                result[relative] = file_fingerprint(path)
            except FileNotFoundError:
                continue
            if len(result) > MAX_SNAPSHOT_FILES:
                raise ContractError(f"workspace snapshot exceeds {MAX_SNAPSHOT_FILES} files; use a smaller cwd")
    git_directory = root / ".git"
    if git_directory.is_dir():
        protected_git_files = [git_directory / name for name in ("HEAD", "config", "index", "packed-refs")]
        refs = git_directory / "refs"
        if refs.is_dir():
            protected_git_files.extend(path for path in refs.rglob("*") if path.is_file())
        for path in protected_git_files:
            if path.is_file():
                result[path.relative_to(root).as_posix()] = file_fingerprint(path)
    return result


def protected_relative(relative: str) -> bool:
    parts = Path(relative).parts
    return any(part in {".git", ".codex", ".agents", ".grok"} or part == ".env" or part.startswith(".env.") for part in parts)


def path_allowed(relative: str, allowed: list[str], workspace_write: bool) -> bool:
    if protected_relative(relative):
        return False
    if workspace_write:
        return True
    return any(relative == item or relative.startswith(item.rstrip("/") + "/") for item in allowed)


def changed_paths(before: dict[str, str], after: dict[str, str], allowed: list[str], workspace_write: bool) -> tuple[list[str], list[str]]:
    changed = sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))
    violations = [key for key in changed if not path_allowed(key, allowed, workspace_write)]
    return changed, violations


def original_baseline(previous: dict[str, Any] | None) -> dict[str, str | None]:
    if previous is None:
        return {}
    raw = previous.get("baseline_fingerprints")
    if not isinstance(raw, dict):
        raise ContractError("receipt lacks the original workspace baseline; start a new run instead of resuming")
    if not all(isinstance(path, str) and (fingerprint is None or isinstance(fingerprint, str)) for path, fingerprint in raw.items()):
        raise ContractError("receipt contains an invalid workspace baseline")
    return dict(raw)


def cumulative_changes(
    baseline: dict[str, str | None],
    before: dict[str, str],
    after: dict[str, str],
    allowed: list[str],
    workspace_write: bool,
) -> tuple[list[str], list[str], dict[str, str | None]]:
    updated = dict(baseline)
    for path in set(before) | set(after):
        if before.get(path) != after.get(path) and path not in updated:
            updated[path] = before.get(path)
    changed = sorted(path for path, fingerprint in updated.items() if fingerprint != after.get(path))
    violations = [path for path in changed if not path_allowed(path, allowed, workspace_write)]
    return changed, violations, updated


def stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        try:
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass


def read_capture(stream: Any) -> str:
    stream.flush()
    size = stream.tell()
    stream.seek(max(0, size - MAX_CAPTURE_BYTES))
    return stream.read().decode("utf-8", errors="replace")


def run_process(arguments: list[str], cwd: Path, timeout: int) -> tuple[int, str, str, bool]:
    creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen(
            arguments,
            cwd=cwd,
            env=clean_environment(),
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            start_new_session=os.name != "nt",
            creationflags=creation_flags,
        )
        timed_out = False
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            stop_process(process)
        return process.returncode if process.returncode is not None else -1, read_capture(stdout), read_capture(stderr), timed_out


def parse_stream(stdout: str, stderr: str, code: int, timed_out: bool) -> dict[str, Any]:
    summary_parts: list[str] = []
    errors: list[str] = []
    tools: list[dict[str, Any]] = []
    session_id: str | None = None
    actual_model: str | None = None
    terminal = False
    success = False
    usage: Any = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_type = event.get("type")
        if event_type == "text":
            summary_parts.append(str(event.get("data", "")))
        elif event_type == "tool_call":
            raw_input = event.get("rawInput")
            name = "web_search" if isinstance(raw_input, dict) and raw_input.get("variant") == "WebSearch" else event.get("toolName")
            tools.append({"id": event.get("toolCallId"), "name": name, "status": event.get("status")})
        elif event_type == "tool_call_update":
            tool = next((item for item in tools if item.get("id") == event.get("toolCallId")), None)
            if tool is not None:
                if event.get("status"):
                    tool["status"] = event["status"]
                raw_output = event.get("rawOutput")
                action = raw_output.get("action", {}) if isinstance(raw_output, dict) else {}
                if action.get("type") == "search":
                    tool["name"] = "web_search"
                    tool["sources"] = [
                        item.get("url") for item in action.get("sources", []) if item.get("type") == "url" and item.get("url")
                    ]
        elif event_type == "error":
            errors.append(str(event.get("message", "provider_error")))
        elif event_type == "end":
            terminal = True
            success = event.get("stopReason") == "end_turn"
            session_id = event.get("sessionId") or session_id
            usage = event.get("usage")
            model_usage = event.get("modelUsage", {})
            if isinstance(model_usage, dict) and model_usage:
                actual_model = next(iter(model_usage))

    diagnostic = "\n".join([stderr, *errors])
    if timed_out:
        status = "timed_out"
    elif terminal and success and code == 0 and not errors:
        status = "executed"
    elif re.search(r"authentication required|not logged in|login required|unauthorized|auth.*expired", diagnostic, re.I):
        status = "blocked_auth"
    elif re.search(r"quota.*exhaust|rate.?limit|usage.?limit|insufficient.?credit|limit reached", diagnostic, re.I):
        status = "blocked_quota"
    elif re.search(r"permission.?denied|requires approval|approval required|operation not permitted", diagnostic, re.I):
        status = "blocked_permission"
    elif re.search(r"connection.*failed|connection.*reset|failed to get profile|stream was interrupted|\bEOF\b|network.*(?:error|issue)|could not resolve", diagnostic, re.I):
        status = "blocked_network"
    else:
        status = "failed"
    summary = "".join(summary_parts)[-12_000:]
    sources = set(URL_PATTERN.findall(summary))
    for tool in tools:
        sources.update(tool.get("sources", []))
    return {
        "status": status,
        "session_id": session_id,
        "actual_model": actual_model,
        "summary": summary,
        "sources": sorted(sources),
        "tools": tools,
        "errors": errors,
        "stderr": stderr[-4000:],
        "exit_code": code,
        "usage": usage,
        "terminal": terminal,
    }


def run_checks(task: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for check in task["checks"]:
        started = time.monotonic()
        try:
            completed = subprocess.run(
                check["argv"],
                cwd=task["cwd"],
                env=clean_environment(),
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=check["timeout_seconds"],
                check=False,
            )
            results.append(
                {
                    "argv": check["argv"],
                    "exit_code": completed.returncode,
                    "stdout": completed.stdout[-8000:],
                    "stderr": completed.stderr[-4000:],
                    "duration_seconds": round(time.monotonic() - started, 3),
                }
            )
        except subprocess.TimeoutExpired as exc:
            results.append(
                {
                    "argv": check["argv"],
                    "exit_code": None,
                    "timed_out": True,
                    "stdout": (exc.stdout or "")[-8000:] if isinstance(exc.stdout, str) else "",
                    "stderr": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
                    "duration_seconds": round(time.monotonic() - started, 3),
                }
            )
        except OSError as exc:
            results.append(
                {
                    "argv": check["argv"],
                    "exit_code": None,
                    "error": str(exc),
                    "duration_seconds": round(time.monotonic() - started, 3),
                }
            )
    return results


def receipt_status(task: dict[str, Any], provider: dict[str, Any], violations: list[str], checks: list[dict[str, Any]]) -> str:
    if violations:
        return "scope_violation"
    if provider["status"] != "executed":
        return provider["status"]
    if any(check.get("exit_code") != 0 for check in checks):
        return "verification_failed"
    if task["mode"] == "research":
        return "needs_source_review"
    if task["mode"] == "frontend":
        return "needs_visual_review"
    return "needs_code_review"


def compact_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    provider = receipt.get("provider", {})
    return {
        "id": receipt.get("task", {}).get("id"),
        "status": receipt.get("status"),
        "session_id": provider.get("session_id"),
        "actual_model": provider.get("actual_model"),
        "changed_paths": receipt.get("changed_paths", []),
        "scope_violations": receipt.get("scope_violations", []),
        "checks": [
            {"argv": item.get("argv"), "exit_code": item.get("exit_code"), "timed_out": item.get("timed_out", False)}
            for item in receipt.get("checks", [])
        ],
        "sources": provider.get("sources", []),
        "summary": provider.get("summary", ""),
        "errors": provider.get("errors", []),
        "receipt": receipt.get("receipt_path"),
    }


def execute(task: dict[str, Any], receipt_path: Path, grok: Path, session_id: str | None, feedback: str | None, previous: dict[str, Any] | None) -> dict[str, Any]:
    root = Path(task["cwd"])
    baseline = original_baseline(previous)
    before = snapshot(root)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as prompt_stream:
        prompt_stream.write(executor_prompt(task, feedback))
        prompt_path = Path(prompt_stream.name)
    try:
        arguments = invocation(task, grok, prompt_path, session_id)
        code, stdout, stderr, timed_out = run_process(arguments, root, task["timeout_seconds"])
    finally:
        prompt_path.unlink(missing_ok=True)
    provider = parse_stream(stdout, stderr, code, timed_out)
    after = snapshot(root)
    changed, violations, baseline = cumulative_changes(
        baseline, before, after, task["allowed_paths"], task["workspace_write"]
    )
    checks = run_checks(task) if not violations and provider["status"] == "executed" else []
    if checks:
        final = snapshot(root)
        changed, violations, baseline = cumulative_changes(
            baseline, before, final, task["allowed_paths"], task["workspace_write"]
        )
    status = receipt_status(task, provider, violations, checks)
    if session_id and provider.get("session_id") and provider["session_id"] != session_id:
        status = "session_mismatch"
        provider["errors"].append("Grok returned a different session id")
    attempt = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": status,
        "provider_status": provider["status"],
        "changed_paths": changed,
        "scope_violations": violations,
        "checks": checks,
    }
    attempts = list(previous.get("attempts", [])) if previous else []
    attempts.append(attempt)
    receipt = {
        "schema_version": 2,
        "task": task,
        "status": status,
        "provider": provider,
        "changed_paths": changed,
        "scope_violations": violations,
        "checks": checks,
        "baseline_fingerprints": baseline,
        "attempts": attempts,
        "receipt_path": str(receipt_path.resolve()),
    }
    save_json(receipt_path, receipt)
    return receipt


def doctor(grok: Path) -> dict[str, Any]:
    version = subprocess.run([str(grok), "--version"], capture_output=True, text=True, timeout=15, check=False)
    help_result = subprocess.run([str(grok), "--help"], capture_output=True, text=True, timeout=15, check=False)
    help_text = help_result.stdout + help_result.stderr
    missing = [flag for flag in REQUIRED_GROK_FLAGS if flag not in help_text]
    return {
        "ok": version.returncode == 0 and help_result.returncode == 0 and not missing,
        "binary": str(grok),
        "version": (version.stdout or version.stderr).strip().splitlines()[0] if (version.stdout or version.stderr).strip() else None,
        "missing_required_flags": missing,
        "authentication": "not probed; a real bounded task verifies subscription readiness",
        "permission_boundary": "workspace sandbox with declared paths and commands",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grok-bin", help="Grok CLI path; defaults to GROK_BIN, PATH, or a standard user install")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor")
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--task", required=True, type=Path)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--task", required=True, type=Path)
    run_parser.add_argument("--receipt", type=Path)
    resume_parser = subparsers.add_parser("resume")
    resume_parser.add_argument("--receipt", required=True, type=Path)
    resume_parser.add_argument("--feedback", required=True, type=Path)
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--receipt", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        if arguments.command == "status":
            emit(compact_receipt(read_json(arguments.receipt.resolve())))
            return 0
        if arguments.command == "validate":
            task_file = arguments.task.resolve()
            task = normalize_task(read_json(task_file), task_file)
            emit({"ok": True, "task": task})
            return 0
        grok = find_grok(arguments.grok_bin)
        if arguments.command == "doctor":
            result = doctor(grok)
            emit(result)
            return 0 if result["ok"] else 1
        if arguments.command == "run":
            task_file = arguments.task.resolve()
            task = normalize_task(read_json(task_file), task_file)
            receipt_path = arguments.receipt.resolve() if arguments.receipt else task_file.with_suffix(task_file.suffix + ".receipt.json")
            if receipt_path.exists():
                raise ContractError(f"receipt already exists: {receipt_path}; use resume or a new task id")
            receipt = execute(task, receipt_path, grok, None, None, None)
            emit(compact_receipt(receipt))
            return 0 if receipt["status"].startswith("needs_") else 2
        if arguments.command == "resume":
            receipt_path = arguments.receipt.resolve()
            previous = read_json(receipt_path)
            session_id = previous.get("provider", {}).get("session_id")
            if not session_id:
                raise ContractError("receipt has no Grok session id; refusing to start a replacement session")
            feedback = arguments.feedback.resolve().read_text(encoding="utf-8")
            if not feedback.strip():
                raise ContractError("feedback must not be empty")
            if len(previous.get("attempts", [])) >= 3:
                raise ContractError("repair limit reached; inspect the repeated blocker before another model call")
            saved_task = previous.get("task")
            if not isinstance(saved_task, dict):
                raise ContractError("receipt has no normalized task")
            task = normalize_task(saved_task, receipt_path)
            receipt = execute(task, receipt_path, grok, session_id, feedback, previous)
            emit(compact_receipt(receipt))
            return 0 if receipt["status"].startswith("needs_") else 2
    except (ContractError, OSError, subprocess.SubprocessError) as exc:
        emit({"ok": False, "error": str(exc)})
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
