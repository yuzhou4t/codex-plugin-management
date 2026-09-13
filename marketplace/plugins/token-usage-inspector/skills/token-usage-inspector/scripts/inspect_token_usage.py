#!/usr/bin/env python3
"""Inspect native token counters in local Codex rollout JSONL logs."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


FINAL_PHASES = {"final", "final_answer"}
WRAPPER_PREFIXES = ("<environment_context>", "<recommended_plugins>")


def codex_home(value: str | None) -> Path:
    if value:
        return Path(value).expanduser()
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def session_files(root: Path) -> list[Path]:
    sessions = root / "sessions"
    if not sessions.is_dir():
        raise FileNotFoundError(f"Codex sessions directory not found: {sessions}")
    return sorted(sessions.rglob("rollout-*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)


def resolve_session(args: argparse.Namespace) -> Path:
    if args.session:
        path = Path(args.session).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Session file not found: {path}")
        return path

    files = session_files(codex_home(args.codex_home))
    if args.thread_id:
        matches = [path for path in files if args.thread_id in path.name]
        if not matches:
            raise FileNotFoundError(f"No local rollout log found for task ID: {args.thread_id}")
        return matches[0]
    if not files:
        raise FileNotFoundError("No local Codex rollout logs found")
    return files[0]


def load_records(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # A live writer may leave only the final line temporarily incomplete.
                if line_number == sum(1 for _ in path.open(encoding="utf-8")):
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


def usage_fields(usage: dict[str, Any]) -> dict[str, int]:
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


def parse_usage(path: Path, include_prompt: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    prompts: dict[str, list[str]] = defaultdict(list)
    final_turns: set[str] = set()
    call_counts: dict[str, int] = defaultdict(int)
    call_rows: list[dict[str, Any]] = []
    turn_order: list[str] = []
    latest_by_turn: dict[str, dict[str, Any]] = {}

    for record in load_records(path):
        payload = record.get("payload", {})
        if record.get("type") == "response_item" and payload.get("type") == "message":
            metadata = payload.get("internal_chat_message_metadata_passthrough", {})
            turn_id = metadata.get("turn_id")
            if turn_id and payload.get("role") == "user":
                prompts[turn_id].append(content_text(payload))
            elif turn_id and payload.get("role") == "assistant" and payload.get("phase") in FINAL_PHASES:
                final_turns.add(turn_id)

        if record.get("type") != "token_usage_record":
            continue
        turn_id = payload.get("turn_id")
        if not turn_id:
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
                **usage_fields(payload.get("usage", {})),
            }
        )
        latest_by_turn[turn_id] = {
            "timestamp_utc": record.get("timestamp", ""),
            **usage_fields(payload.get("turn_token_usage", {})),
        }

    turn_rows = []
    for number, turn_id in enumerate(turn_order, start=1):
        row: dict[str, Any] = {
            "turn": number,
            "status": "complete" if turn_id in final_turns else "in_progress",
            "turn_id": turn_id,
            **latest_by_turn[turn_id],
        }
        if include_prompt:
            row["prompt"] = prompt_preview(prompts[turn_id])
        turn_rows.append(row)
    return turn_rows, call_rows


def table(rows: list[dict[str, Any]], granularity: str) -> str:
    if not rows:
        return "No token usage records found."
    columns = ["turn"]
    if granularity == "call":
        columns.append("call")
    else:
        columns.append("status")
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
    widths = {
        column: max(len(column), *(len(f"{row.get(column, ''):,}") if isinstance(row.get(column), int) else len(str(row.get(column, ""))) for row in rows))
        for column in columns
    }
    result = ["  ".join(column.ljust(widths[column]) for column in columns)]
    result.append("  ".join("-" * widths[column] for column in columns))
    for row in rows:
        values = []
        for column in columns:
            value = row.get(column, "")
            rendered = f"{value:,}" if isinstance(value, int) else str(value)
            values.append(rendered.rjust(widths[column]) if column.endswith("tokens") or column in {"turn", "call"} else rendered.ljust(widths[column]))
        result.append("  ".join(values))
    return "\n".join(result)


def serialize(rows: list[dict[str, Any]], output_format: str, granularity: str) -> str:
    if output_format == "json":
        return json.dumps(rows, ensure_ascii=False, indent=2)
    if output_format == "csv":
        if not rows:
            return ""
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue()
    return table(rows, granularity)


def list_local_sessions(args: argparse.Namespace) -> None:
    rows = []
    for path in session_files(codex_home(args.codex_home))[: args.limit]:
        thread_id = path.stem.split("-")[-5:]
        row = {
            "modified_local": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
            "task_id": "-".join(thread_id),
            "path": str(path),
        }
        if args.include_prompt:
            turns, _ = parse_usage(path, include_prompt=True)
            row["prompt"] = turns[-1].get("prompt", "") if turns else ""
        rows.append(row)
    print(json.dumps(rows, ensure_ascii=False, indent=2) if args.format == "json" else table_for_sessions(rows))


def table_for_sessions(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No local Codex sessions found."
    headers = list(rows[0])
    widths = {header: max(len(header), *(len(str(row.get(header, ""))) for row in rows)) for header in headers}
    lines = ["  ".join(header.ljust(widths[header]) for header in headers)]
    lines.append("  ".join("-" * widths[header] for header in headers))
    lines.extend("  ".join(str(row.get(header, "")).ljust(widths[header]) for header in headers) for row in rows)
    return "\n".join(lines)


def write_snapshot(args: argparse.Namespace, path: Path) -> None:
    turn_rows, call_rows = parse_usage(path, args.include_prompt)
    rows = turn_rows if args.granularity == "turn" else call_rows
    rendered = serialize(rows, args.format, args.granularity)
    heading = f"Session: {path}\nUpdated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
    content = rendered if args.format in {"csv", "json"} else f"{heading}\n{rendered}"
    if args.output:
        Path(args.output).expanduser().write_text(content, encoding="utf-8")
    else:
        if args.watch and sys.stdout.isatty():
            print("\033[2J\033[H", end="")
        print(content)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--session", help="Exact rollout JSONL path")
    target.add_argument("--thread-id", help="Codex task/thread ID")
    target.add_argument("--latest", action="store_true", help="Use the most recently modified local session")
    parser.add_argument("--codex-home", help="Override CODEX_HOME")
    parser.add_argument("--granularity", choices=("turn", "call"), default="turn")
    parser.add_argument("--format", choices=("table", "csv", "json"), default="table")
    parser.add_argument("--output", help="Write the snapshot to a file")
    parser.add_argument("--watch", type=float, metavar="SECONDS", help="Refresh until interrupted")
    parser.add_argument("--include-prompt", action="store_true", help="Include a short user-prompt preview")
    parser.add_argument("--list-sessions", action="store_true", help="List recent local sessions and exit")
    parser.add_argument("--limit", type=int, default=20, help="Maximum sessions to list")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.list_sessions:
            list_local_sessions(args)
            return 0
        path = resolve_session(args)
        if args.watch is not None and args.watch <= 0:
            raise ValueError("--watch must be greater than zero")
        while True:
            write_snapshot(args, path)
            if args.watch is None:
                return 0
            time.sleep(args.watch)
    except KeyboardInterrupt:
        return 0
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
