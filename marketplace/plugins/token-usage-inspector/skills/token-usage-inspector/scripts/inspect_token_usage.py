#!/usr/bin/env python3
"""Inspect current and historical token usage in local Codex rollout logs."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time as datetime_time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


FINAL_PHASES = {"final", "final_answer"}
WRAPPER_PREFIXES = ("<environment_context>", "<recommended_plugins>")
USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)
GROUP_FIELDS = {"month", "day", "model", "project", "task", "source"}


@dataclass(frozen=True)
class SessionInfo:
    path: Path
    task_id: str
    started: str
    project: str
    source: str
    spawned: bool
    guardian: bool


def codex_home(value: str | None) -> Path:
    if value:
        return Path(value).expanduser()
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def session_files(root: Path, include_archived: bool = True) -> list[Path]:
    directories = [root / "sessions"]
    if include_archived:
        directories.append(root / "archived_sessions")
    files: list[Path] = []
    for directory in directories:
        if directory.is_dir():
            files.extend(directory.rglob("rollout-*.jsonl"))
    if not files:
        names = "sessions/ and archived_sessions/" if include_archived else "sessions/"
        raise FileNotFoundError(f"No rollout logs found under {root} ({names})")
    return sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)


def session_info(path: Path) -> SessionInfo | None:
    try:
        for record in load_records(path):
            if record.get("type") != "session_meta":
                continue
            payload = record.get("payload", {})
            source_value = payload.get("source")
            source_text = json.dumps(source_value, ensure_ascii=False) if isinstance(source_value, (dict, list)) else str(source_value or "")
            spawned = is_spawned_source(source_value)
            guardian = "guardian" in source_text.lower()
            source = "spawned" if spawned else "guardian" if guardian else "root"
            return SessionInfo(
                path=path,
                task_id=str(payload.get("id") or task_id_from_name(path)),
                started=str(payload.get("timestamp") or record.get("timestamp") or ""),
                project=str(payload.get("cwd") or ""),
                source=source,
                spawned=spawned,
                guardian=guardian,
            )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read rollout metadata from {path}: {exc}") from exc
    return None


def is_spawned_source(source: Any) -> bool:
    subagent = source.get("subagent") if isinstance(source, dict) else None
    return isinstance(subagent, dict) and "thread_spawn" in subagent


def task_id_from_name(path: Path) -> str:
    parts = path.stem.split("-")
    return "-".join(parts[-5:]) if len(parts) >= 5 else path.stem


def all_session_info(root: Path, include_archived: bool = True) -> list[SessionInfo]:
    result = []
    for path in session_files(root, include_archived=include_archived):
        info = session_info(path)
        if info:
            result.append(info)
    return result


def resolve_session(args: argparse.Namespace) -> Path:
    if args.session:
        path = Path(args.session).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Session file not found: {path}")
        return path
    files = session_files(codex_home(args.codex_home), include_archived=not getattr(args, "active_only", False))
    if args.thread_id:
        matches = [path for path in files if args.thread_id in path.name]
        if not matches:
            raise FileNotFoundError(f"No local rollout log found for task ID: {args.thread_id}")
        return matches[0]
    if not args.latest:
        raise ValueError("Choose --session, --thread-id, or explicit --latest; use --list-sessions to identify a task")
    if not files:
        raise FileNotFoundError("No local Codex rollout logs found")
    return files[0]


def load_records(path: Path) -> Iterable[dict[str, Any]]:
    snapshot = path.read_bytes()
    archived = "archived_sessions" in path.parts or "archived_sessions" in path.resolve().parts
    lines = snapshot.splitlines()
    for index, raw_line in enumerate(lines):
        try:
            yield json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            # The one immutable read can end inside the live writer's final
            # UTF-8 codepoint or JSON object. A malformed terminated/interior
            # line is persistent corruption and must still surface. Archived
            # logs are immutable, so even an unterminated fragment is corrupt.
            if not archived and index == len(lines) - 1 and not snapshot.endswith((b"\n", b"\r")):
                return
            raise


def content_text(payload: dict[str, Any]) -> str:
    parts = []
    for item in payload.get("content", []):
        if isinstance(item, dict) and item.get("text"):
            parts.append(str(item["text"]))
    return " ".join(parts).replace("\r", " ").replace("\n", " ").strip()


def prompt_preview(messages: list[str]) -> str:
    useful = [message for message in messages if not message.startswith(WRAPPER_PREFIXES)]
    text = useful[-1] if useful else (messages[-1] if messages else "")
    return text[:120] + ("…" if len(text) > 120 else "")


def append_prompt(messages: list[str], text: str) -> None:
    normalized = " ".join(text.split())
    if normalized and (not messages or messages[-1] != normalized):
        messages.append(normalized)


def usage_fields(usage: dict[str, Any] | None) -> dict[str, int]:
    usage = usage or {}
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    cached = int(usage.get("cached_input_tokens", 0) or 0)
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached,
        "uncached_input_tokens": input_tokens - cached,
        "cache_write_input_tokens": int(usage.get("cache_write_input_tokens", 0) or 0),
        "output_tokens": int(usage.get("output_tokens", 0) or 0),
        "reasoning_output_tokens": int(usage.get("reasoning_output_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", 0) or 0),
    }


def base_usage(usage: dict[str, Any] | None) -> dict[str, int]:
    fields = usage_fields(usage)
    return {field: fields[field] for field in USAGE_FIELDS}


def subtract_usage(current: dict[str, int], prior: dict[str, int]) -> dict[str, int]:
    return {field: current[field] - prior[field] for field in USAGE_FIELDS}


def usage_delta(total: dict[str, Any], baseline: dict[str, int]) -> dict[str, int]:
    counters = {key: int(total.get(key, 0) or 0) for key in USAGE_FIELDS}
    if any(counters[key] < baseline.get(key, 0) for key in USAGE_FIELDS):
        baseline = {}
    return {key: counters[key] - baseline.get(key, 0) for key in USAGE_FIELDS}


def parse_usage(path: Path, include_prompt: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Prefer native calls per rollout, excluding spawned-agent inherited replay."""
    records = list(load_records(path))
    spawned = any(
        record.get("type") == "session_meta" and is_spawned_source(record.get("payload", {}).get("source"))
        for record in records
    )
    child_active = not spawned
    active_records = []
    previous_total_usage = base_usage({})
    for record in records:
        payload = record.get("payload", {})
        if record.get("type") == "inter_agent_communication_metadata":
            child_active = True
        if not child_active:
            if record.get("type") == "event_msg" and payload.get("type") == "token_count":
                info = payload.get("info")
                if isinstance(info, dict) and isinstance(info.get("total_token_usage"), dict):
                    previous_total_usage = base_usage(info["total_token_usage"])
            continue
        active_records.append(record)
    use_native = any(
        record.get("type") == "token_usage_record"
        and record.get("payload", {}).get("turn_id")
        and isinstance(record.get("payload", {}).get("usage"), dict)
        for record in active_records
    )
    prompts: dict[str, list[str]] = defaultdict(list)
    terminal_status: dict[str, str] = {}
    pending_prompts: list[str] = []
    call_counts: dict[str, int] = defaultdict(int)
    call_rows: list[dict[str, Any]] = []
    turn_order: list[str] = []
    latest_by_turn: dict[str, dict[str, Any]] = {}
    active_turn_id: str | None = None
    baseline_by_turn: dict[str, dict[str, int]] = {}

    for record in active_records:
        payload = record.get("payload", {})
        if record.get("type") == "event_msg":
            event_type = payload.get("type")
            if event_type == "user_message" and include_prompt:
                message = payload.get("message")
                if isinstance(message, str):
                    append_prompt(prompts[active_turn_id] if active_turn_id else pending_prompts, message)
            if event_type == "task_started" and payload.get("turn_id"):
                active_turn_id = str(payload["turn_id"])
                baseline_by_turn[active_turn_id] = dict(previous_total_usage)
                if active_turn_id not in latest_by_turn:
                    turn_order.append(active_turn_id)
                    latest_by_turn[active_turn_id] = {
                        "timestamp_utc": record.get("timestamp", ""),
                        **usage_fields({}),
                    }
                if pending_prompts:
                    prompts[active_turn_id].extend(pending_prompts)
                    pending_prompts.clear()
            elif event_type in {"task_complete", "turn_aborted"}:
                terminal_turn_id = payload.get("turn_id") or active_turn_id
                if terminal_turn_id:
                    terminal_turn_id = str(terminal_turn_id)
                    terminal_status[terminal_turn_id] = "complete" if event_type == "task_complete" else "aborted"
                if active_turn_id == terminal_turn_id:
                    active_turn_id = None
            elif event_type == "token_count" and active_turn_id and not use_native:
                info = payload.get("info")
                if not isinstance(info, dict):
                    continue
                last_usage = info.get("last_token_usage")
                total_usage = info.get("total_token_usage")
                if not isinstance(last_usage, dict) or not isinstance(total_usage, dict):
                    continue
                current = base_usage(total_usage)
                # Rate-limit updates can repeat the preceding last_token_usage.
                # Only an advancing cumulative snapshot represents another call.
                if current == previous_total_usage:
                    continue
                if active_turn_id not in latest_by_turn:
                    turn_order.append(active_turn_id)
                call_counts[active_turn_id] += 1
                call_rows.append(
                    {
                        "turn": turn_order.index(active_turn_id) + 1,
                        "call": call_counts[active_turn_id],
                        "turn_id": active_turn_id,
                        "timestamp_utc": record.get("timestamp", ""),
                        **usage_fields(last_usage),
                    }
                )
                latest_by_turn[active_turn_id] = {
                    "timestamp_utc": record.get("timestamp", ""),
                    **usage_fields(usage_delta(total_usage, baseline_by_turn.get(active_turn_id, {}))),
                }
                previous_total_usage = current
                continue
        if record.get("type") == "response_item" and payload.get("type") == "message":
            metadata = payload.get("internal_chat_message_metadata_passthrough", {})
            turn_id = metadata.get("turn_id") if isinstance(metadata, dict) else None
            if payload.get("role") == "user" and include_prompt:
                message = content_text(payload)
                if turn_id:
                    append_prompt(prompts[str(turn_id)], message)
                else:
                    append_prompt(prompts[active_turn_id] if active_turn_id else pending_prompts, message)
            elif turn_id and payload.get("role") == "assistant" and payload.get("phase") in FINAL_PHASES:
                terminal_status[str(turn_id)] = "complete"

        if record.get("type") != "token_usage_record" or not use_native:
            continue
        turn_id = payload.get("turn_id")
        if not turn_id or not isinstance(payload.get("usage"), dict):
            continue
        if turn_id not in latest_by_turn:
            turn_order.append(turn_id)
        call_counts[turn_id] += 1
        call_rows.append(
            {
                "turn": turn_order.index(turn_id) + 1,
                "call": call_counts[turn_id],
                "turn_id": turn_id,
                "timestamp_utc": record.get("timestamp", ""),
                **usage_fields(payload.get("usage")),
            }
        )
        turn_usage = payload.get("turn_token_usage")
        if not isinstance(turn_usage, dict):
            prior = latest_by_turn.get(turn_id, {})
            current = base_usage(payload["usage"])
            turn_usage = {field: prior.get(field, 0) + current[field] for field in USAGE_FIELDS}
        latest_by_turn[turn_id] = {
            "timestamp_utc": record.get("timestamp", ""),
            **usage_fields(turn_usage),
        }

    turn_rows = []
    previews = {turn_id: prompt_preview(prompts[turn_id]) for turn_id in turn_order} if include_prompt else {}
    for number, turn_id in enumerate(turn_order, start=1):
        row: dict[str, Any] = {
            "turn": number,
            "status": terminal_status.get(turn_id, "in_progress"),
            "turn_id": turn_id,
            **latest_by_turn[turn_id],
        }
        if include_prompt:
            row["prompt"] = previews[turn_id]
        turn_rows.append(row)
    if include_prompt:
        for row in call_rows:
            row["prompt"] = previews.get(str(row["turn_id"]), "")
    return turn_rows, call_rows


def timezone_from_name(name: str) -> timezone | ZoneInfo | None:
    if name == "local":
        # astimezone(None) asks the OS for the offset at the timestamp being
        # converted, preserving historical DST rules on POSIX and Windows.
        return None
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(
            f"Unknown or unavailable timezone: {name}. If IANA timezone data is missing "
            "(common on Windows), run 'python -m pip install tzdata' in the Python "
            "environment used for this script; otherwise check the timezone name."
        ) from exc


def parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_boundary(value: str | None, zone: timezone | ZoneInfo | None, *, end: bool) -> datetime | None:
    if not value:
        return None
    try:
        if len(value) == 10:
            parsed_date = date.fromisoformat(value)
            boundary = datetime.combine(parsed_date, datetime_time.min)
            if end:
                boundary += timedelta(days=1)
            return boundary.replace(tzinfo=zone) if zone is not None else boundary.astimezone()
        boundary = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid {'--to' if end else '--from'} value: {value}") from exc
    if boundary.tzinfo is None and zone is not None:
        return boundary.replace(tzinfo=zone)
    return boundary.astimezone(zone)


def project_matches(recorded: str, requested: str | None, include_subdirs: bool) -> bool:
    if requested is None:
        return True
    requested = os.path.normpath(os.path.expanduser(requested))
    recorded = os.path.normpath(recorded) if recorded else ""
    return recorded == requested or (include_subdirs and recorded.startswith(os.path.join(requested, "")))


def normalize_repeat(values: list[str] | None) -> list[str]:
    result = []
    for value in values or []:
        result.extend(item.strip() for item in value.split(",") if item.strip())
    return result


def read_usage_events(info: SessionInfo) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return native call deltas and legacy cumulative snapshots for one file."""
    native: list[dict[str, Any]] = []
    legacy: list[dict[str, Any]] = []
    child_active = not info.spawned
    model = "codex-auto-review" if info.guardian else "unknown"
    for record in load_records(info.path):
        payload = record.get("payload", {})
        record_type = record.get("type")
        if record_type == "turn_context":
            model = str(payload.get("model") or model)
        elif record_type == "inter_agent_communication_metadata":
            child_active = True
        elif record_type == "token_usage_record" and isinstance(payload.get("usage"), dict):
            if info.spawned and not child_active:
                continue
            native.append(
                {
                    "timestamp": str(record.get("timestamp") or ""),
                    "model": model,
                    "usage": base_usage(payload.get("usage")),
                    "response_id": str(payload.get("response_id") or ""),
                    "turn_id": str(payload.get("turn_id") or ""),
                }
            )
        elif record_type == "event_msg" and payload.get("type") == "token_count":
            usage_info = payload.get("info")
            if not isinstance(usage_info, dict) or not isinstance(usage_info.get("total_token_usage"), dict):
                continue
            legacy.append(
                {
                    "timestamp": str(record.get("timestamp") or ""),
                    "model": model,
                    "total": base_usage(usage_info.get("total_token_usage")),
                    "last": base_usage(usage_info.get("last_token_usage")),
                    "child_active": child_active,
                }
            )
    return native, legacy


def selected_infos(args: argparse.Namespace) -> list[SessionInfo]:
    if args.session or args.latest or (args.thread_id and not args.historical):
        path = resolve_session(args)
        infos = [session_info(path) or SessionInfo(path, task_id_from_name(path), "", "", "root", False, False)]
    else:
        infos = all_session_info(codex_home(args.codex_home), include_archived=not getattr(args, "active_only", False))
    excluded = set(normalize_repeat(args.exclude_thread))
    return [
        info
        for info in infos
        if project_matches(info.project, args.project, args.include_subdirs)
        and info.task_id not in excluded
        and (not args.thread_id or args.thread_id in info.task_id or args.thread_id in info.path.name)
    ]


def collect_historical_events(args: argparse.Namespace, infos: list[SessionInfo] | None = None) -> list[dict[str, Any]]:
    if infos is None:
        infos = selected_infos(args)
    result: list[dict[str, Any]] = []
    seen_native: set[tuple[Any, ...]] = set()
    seen_legacy: set[tuple[Any, ...]] = set()
    for info in sorted(infos, key=lambda item: str(item.path)):
        try:
            native, legacy = read_usage_events(info)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Cannot read rollout usage from {info.path}: {exc}") from exc
        if native:
            for event in native:
                identity = (info.task_id, event["response_id"]) if event["response_id"] else (
                    info.task_id,
                    None,
                    event["timestamp"],
                    event["turn_id"],
                    event["model"],
                    tuple(event["usage"][field] for field in USAGE_FIELDS),
                )
                if identity in seen_native:
                    continue
                seen_native.add(identity)
                result.append(make_event(info, event["timestamp"], event["model"], "native", event["usage"]))
            continue

        # Old token_count records are cumulative within each rollout file.
        prior: dict[str, int] | None = None
        for event in legacy:
            current = event["total"]
            if info.spawned and not event["child_active"]:
                prior = current
                continue
            if prior is None:
                delta = event["last"] if event["last"]["total_tokens"] else current
            else:
                delta = subtract_usage(current, prior)
                if any(value < 0 for value in delta.values()):
                    delta = current
            prior = current
            if delta["total_tokens"] <= 0:
                continue
            identity = (info.task_id, event["timestamp"], event["model"], tuple(current[field] for field in USAGE_FIELDS))
            if identity in seen_legacy:
                continue
            seen_legacy.add(identity)
            result.append(make_event(info, event["timestamp"], event["model"], "legacy", delta))
    return result


def make_event(info: SessionInfo, timestamp: str, model: str, record_source: str, usage: dict[str, int]) -> dict[str, Any]:
    return {
        "timestamp": timestamp,
        "model": model,
        "project": info.project,
        "task": info.task_id,
        "source": info.source,
        "file": str(info.path),
        "record_source": record_source,
        **usage_fields(usage),
    }


def aggregate_usage(args: argparse.Namespace, infos: list[SessionInfo] | None = None) -> list[dict[str, Any]]:
    zone = timezone_from_name(args.timezone)
    start = parse_boundary(args.from_time, zone, end=False)
    end = parse_boundary(args.to_time, zone, end=True)
    if start and end and start >= end:
        raise ValueError("--from must be earlier than --to")
    models = set(normalize_repeat(args.model))
    groups = normalize_repeat(args.group_by) or ["month", "model"]
    invalid = [group for group in groups if group not in GROUP_FIELDS]
    if invalid:
        raise ValueError(f"Unsupported --group-by value: {', '.join(invalid)}")

    buckets: dict[tuple[str, ...], dict[str, Any]] = {}
    seen_tasks: dict[tuple[str, ...], set[str]] = defaultdict(set)
    seen_files: dict[tuple[str, ...], set[str]] = defaultdict(set)
    seen_sources: dict[tuple[str, ...], set[str]] = defaultdict(set)
    for event in collect_historical_events(args, infos):
        stamp = parse_timestamp(event["timestamp"])
        if stamp is None:
            continue
        local = stamp.astimezone(zone)
        if start and local < start:
            continue
        if end and local >= end:
            continue
        if models and event["model"] not in models:
            continue
        dimensions = {
            "month": local.strftime("%Y-%m"),
            "day": local.strftime("%Y-%m-%d"),
            "model": event["model"],
            "project": event["project"] or "(unknown)",
            "task": event["task"],
            "source": event["source"],
        }
        key = tuple(dimensions[group] for group in groups)
        if key not in buckets:
            buckets[key] = {group: dimensions[group] for group in groups}
            buckets[key].update({"tasks": 0, "files": 0, "usage_records": 0, "record_source": "", **usage_fields({})})
        row = buckets[key]
        row["usage_records"] += 1
        for field in (*USAGE_FIELDS, "uncached_input_tokens"):
            row[field] += event[field]
        seen_tasks[key].add(event["task"])
        seen_files[key].add(event["file"])
        seen_sources[key].add(event["record_source"])

    rows = []
    for key in sorted(buckets):
        row = buckets[key]
        row["tasks"] = len(seen_tasks[key])
        row["files"] = len(seen_files[key])
        row["record_source"] = "+".join(sorted(seen_sources[key]))
        rows.append(row)
    return rows


def generic_table(rows: list[dict[str, Any]], empty_message: str = "No matching token usage records found.") -> str:
    if not rows:
        return empty_message
    columns = list(rows[0])
    widths = {
        column: max(
            len(column),
            *(len(f"{row.get(column, ''):,}") if isinstance(row.get(column), int) else len(str(row.get(column, ""))) for row in rows),
        )
        for column in columns
    }
    lines = ["  ".join(column.ljust(widths[column]) for column in columns)]
    lines.append("  ".join("-" * widths[column] for column in columns))
    numeric = {column for column in columns if any(isinstance(row.get(column), int) for row in rows)}
    for row in rows:
        rendered = []
        for column in columns:
            value = row.get(column, "")
            text = f"{value:,}" if isinstance(value, int) else str(value)
            rendered.append(text.rjust(widths[column]) if column in numeric else text.ljust(widths[column]))
        lines.append("  ".join(rendered))
    return "\n".join(lines)


def table(rows: list[dict[str, Any]], granularity: str) -> str:
    if not rows:
        return "No native token usage records found."
    columns = ["turn", "call" if granularity == "call" else "status"]
    columns.extend(
        [
            "input_tokens",
            "cached_input_tokens",
            "uncached_input_tokens",
            "output_tokens",
            "reasoning_output_tokens",
            "total_tokens",
        ]
    )
    if "prompt" in rows[0]:
        columns.append("prompt")
    return generic_table([{column: row.get(column, "") for column in columns} for row in rows])


def serialize(rows: list[dict[str, Any]], output_format: str, granularity: str | None = None) -> str:
    if output_format == "json":
        return json.dumps(rows, ensure_ascii=False, indent=2)
    if output_format == "csv":
        if not rows:
            return ""
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue()
    return table(rows, granularity) if granularity else generic_table(rows)


def list_local_sessions(args: argparse.Namespace) -> None:
    files = session_files(codex_home(args.codex_home))
    if args.output:
        output = Path(args.output).expanduser()
        if any(paths_alias(output, source) for source in files):
            raise ValueError("--output must not alias a native Codex rollout log")
    rows = []
    listed_files = session_files(codex_home(args.codex_home), include_archived=not getattr(args, "active_only", False))
    for path in listed_files[: args.limit]:
        info = session_info(path) or SessionInfo(path, task_id_from_name(path), "", "", "root", False, False)
        row = {
            "modified_local": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
            "task_id": info.task_id,
            "path": str(info.path),
            "started": info.started,
            "source": info.source,
            "project": info.project,
        }
        if args.include_prompt:
            turns, _ = parse_usage(info.path, include_prompt=True)
            row["prompt"] = turns[-1].get("prompt", "") if turns else ""
        rows.append(row)
    write_output(args, serialize(rows, args.format))


def list_projects(args: argparse.Namespace) -> None:
    projects: dict[str, dict[str, Any]] = {}
    tasks: dict[str, set[str]] = defaultdict(set)
    files: dict[str, int] = defaultdict(int)
    infos = all_session_info(codex_home(args.codex_home), include_archived=not getattr(args, "active_only", False))
    reject_rollout_output(args, (info.path for info in infos))
    for info in infos:
        project = info.project or "(unknown)"
        projects.setdefault(project, {"project": project, "first_seen": info.started, "last_seen": info.started})
        projects[project]["first_seen"] = min(projects[project]["first_seen"], info.started)
        projects[project]["last_seen"] = max(projects[project]["last_seen"], info.started)
        tasks[project].add(info.task_id)
        files[project] += 1
    rows = []
    for project in sorted(projects):
        rows.append({**projects[project], "tasks": len(tasks[project]), "files": files[project]})
    write_output(args, serialize(rows[: args.limit], args.format))


def write_output(args: argparse.Namespace, rendered: str, heading: str | None = None) -> None:
    content = rendered if args.format in {"csv", "json"} or not heading else f"{heading}\n\n{rendered}"
    if args.output:
        atomic_write_text(Path(args.output).expanduser(), content)
    else:
        if getattr(args, "watch", None) and sys.stdout.isatty():
            print("\033[2J\033[H", end="")
        print(content)


def write_snapshot(args: argparse.Namespace, path: Path) -> None:
    turn_rows, call_rows = parse_usage(path, args.include_prompt)
    rows = turn_rows if args.granularity == "turn" else call_rows
    rendered = serialize(rows, args.format, args.granularity)
    heading = f"Session: {path}\nUpdated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}"
    write_output(args, rendered, heading)


def historical_mode(args: argparse.Namespace) -> bool:
    return bool(
        args.project
        or args.all_sessions
        or args.from_time
        or args.to_time
        or args.group_by
        or args.model
        or args.exclude_thread
        or args.include_subdirs
        or (args.thread_id and args.historical)
    )


def atomic_write_text(target: Path, content: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def paths_alias(left: Path, right: Path) -> bool:
    if left.resolve() == right.resolve():
        return True
    try:
        return left.exists() and right.exists() and os.path.samefile(left, right)
    except OSError:
        return False


def reject_rollout_output(args: argparse.Namespace, sources: Iterable[Path]) -> None:
    if args.output and any(paths_alias(Path(args.output).expanduser(), source) for source in sources):
        raise ValueError("--output must not alias a native Codex rollout log")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--session", help="Exact rollout JSONL path")
    target.add_argument("--thread-id", help="Codex task/thread ID")
    target.add_argument("--latest", action="store_true", help="Use the most recently modified local session")
    target.add_argument("--project", help="Exact recorded working directory for project-wide history")
    target.add_argument("--all-sessions", action="store_true", help="Aggregate every locally available task")
    parser.add_argument("--historical", action="store_true", help="Aggregate all files belonging to --thread-id")
    parser.add_argument("--codex-home", help="Override CODEX_HOME")
    parser.add_argument("--active-only", action="store_true", help="Exclude archived_sessions (archives are included by default)")
    parser.add_argument("--include-subdirs", action="store_true", help="With --project, include recorded child directories")
    parser.add_argument("--from", dest="from_time", help="Start date or ISO datetime, inclusive")
    parser.add_argument("--to", dest="to_time", help="End date inclusive, or ISO datetime exclusive")
    parser.add_argument("--timezone", default="local", help="IANA timezone for dates and grouping (default: local)")
    parser.add_argument("--group-by", action="append", help="Comma-separated: month,day,model,project,task,source")
    parser.add_argument("--model", action="append", help="Exact model filter; repeat or use commas")
    parser.add_argument("--exclude-thread", action="append", help="Task ID to omit; repeat or use commas")
    parser.add_argument("--granularity", choices=("turn", "call"), default="turn")
    parser.add_argument("--format", choices=("table", "csv", "json"), default="table")
    parser.add_argument("--output", help="Write the snapshot/report to a file")
    parser.add_argument("--watch", type=float, metavar="SECONDS", help="Refresh an exact-session view until interrupted")
    parser.add_argument("--include-prompt", action="store_true", help="Include a short prompt preview in exact-session/list views")
    listing = parser.add_mutually_exclusive_group()
    listing.add_argument("--list-sessions", action="store_true", help="List recent local tasks and exit")
    listing.add_argument("--list-projects", action="store_true", help="List recorded project directories and exit")
    parser.add_argument("--limit", type=int, default=20, help="Maximum rows for list commands")
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if historical_mode(args) and not (args.list_sessions or args.list_projects) and not any(
        (args.session, args.thread_id, args.latest, args.project, args.all_sessions)
    ):
        raise ValueError("Choose an explicit scope: --session, --thread-id, --latest, --project, or --all-sessions")
    if args.watch is not None and args.watch <= 0:
        raise ValueError("--watch must be greater than zero")
    if args.watch is not None and historical_mode(args):
        raise ValueError("--watch is only available for an exact-session view")
    if args.historical and not args.thread_id:
        raise ValueError("--historical requires --thread-id")
    if args.include_subdirs and not args.project:
        raise ValueError("--include-subdirs requires --project")
    if args.include_prompt and historical_mode(args):
        raise ValueError("--include-prompt is unavailable in aggregate mode")


def main() -> int:
    args = build_parser().parse_args()
    try:
        validate_args(args)
        if args.list_sessions:
            list_local_sessions(args)
            return 0
        if args.list_projects:
            list_projects(args)
            return 0
        if historical_mode(args):
            infos = selected_infos(args)
            reject_rollout_output(args, (info.path for info in infos))
            rows = aggregate_usage(args, infos)
            write_output(args, serialize(rows, args.format))
            return 0
        path = resolve_session(args)
        if args.output and paths_alias(Path(args.output).expanduser(), path):
            raise ValueError("--output must not alias the selected Codex rollout log")
        if args.watch is not None and args.watch <= 0:
            raise ValueError("--watch must be greater than zero")
        if args.watch is not None and args.format in {"csv", "json"} and not args.output:
            raise ValueError("--watch with CSV or JSON requires --output so each refresh remains one valid document")
        while True:
            write_snapshot(args, path)
            if args.watch is None:
                return 0
            time.sleep(args.watch)
    except KeyboardInterrupt:
        return 0
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
