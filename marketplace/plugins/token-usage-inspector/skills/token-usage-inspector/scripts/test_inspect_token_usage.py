#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import argparse
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


SCRIPT = Path(__file__).with_name("inspect_token_usage.py")
SPEC = importlib.util.spec_from_file_location("inspect_token_usage", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InspectTokenUsageTests(unittest.TestCase):
    def write_rollout(self, records: list[dict]) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        path = directory / "rollout-test.jsonl"
        path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
        return path

    def test_current_event_schema_groups_calls_under_task_started_turns(self) -> None:
        records = [
            {"timestamp": "2026-09-20T00:00:00.000Z", "type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-a"}},
            {"timestamp": "2026-09-20T00:00:01.000Z", "type": "event_msg", "payload": {"type": "token_count", "info": {
                "last_token_usage": {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 10, "reasoning_output_tokens": 4, "total_tokens": 110},
                "total_token_usage": {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 10, "reasoning_output_tokens": 4, "total_tokens": 110},
            }}},
            {"timestamp": "2026-09-20T00:00:02.000Z", "type": "event_msg", "payload": {"type": "token_count", "info": {
                "last_token_usage": {"input_tokens": 50, "cached_input_tokens": 20, "output_tokens": 5, "reasoning_output_tokens": 2, "total_tokens": 55},
                "total_token_usage": {"input_tokens": 150, "cached_input_tokens": 60, "output_tokens": 15, "reasoning_output_tokens": 6, "total_tokens": 165},
            }}},
            {"timestamp": "2026-09-20T00:00:03.000Z", "type": "event_msg", "payload": {"type": "task_complete", "turn_id": "turn-a"}},
            {"timestamp": "2026-09-20T00:01:00.000Z", "type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-b"}},
            {"timestamp": "2026-09-20T00:01:01.000Z", "type": "event_msg", "payload": {"type": "token_count", "info": {
                "last_token_usage": {"input_tokens": 70, "cached_input_tokens": 10, "output_tokens": 7, "reasoning_output_tokens": 3, "total_tokens": 77},
                "total_token_usage": {"input_tokens": 220, "cached_input_tokens": 70, "output_tokens": 22, "reasoning_output_tokens": 9, "total_tokens": 242},
            }}},
        ]
        turns, calls = MODULE.parse_usage(self.write_rollout(records), include_prompt=False)
        self.assertEqual([(row["turn_id"], row["status"], row["total_tokens"]) for row in turns], [
            ("turn-a", "complete", 165),
            ("turn-b", "in_progress", 77),
        ])
        self.assertEqual([row["total_tokens"] for row in calls], [110, 55, 77])
        self.assertEqual(turns[0]["uncached_input_tokens"], 90)
        self.assertEqual(turns[1]["uncached_input_tokens"], 60)

    def test_legacy_token_usage_records_remain_supported(self) -> None:
        records = [{
            "timestamp": "2026-09-20T00:00:01.000Z",
            "type": "token_usage_record",
            "payload": {
                "turn_id": "legacy-turn",
                "usage": {"input_tokens": 40, "cached_input_tokens": 10, "output_tokens": 4, "total_tokens": 44},
                "turn_token_usage": {"input_tokens": 40, "cached_input_tokens": 10, "output_tokens": 4, "total_tokens": 44},
            },
        }]
        turns, calls = MODULE.parse_usage(self.write_rollout(records), include_prompt=False)
        self.assertEqual(turns[0]["turn_id"], "legacy-turn")
        self.assertEqual(turns[0]["total_tokens"], 44)
        self.assertEqual(calls[0]["uncached_input_tokens"], 30)

    def test_live_reader_ignores_only_an_unterminated_final_fragment(self) -> None:
        path = self.write_rollout([{"type": "complete", "payload": {"value": 1}}])
        with path.open("ab") as handle:
            handle.write(b'{"type":"partial"')
        self.assertEqual(list(MODULE.load_records(path)), [{"type": "complete", "payload": {"value": 1}}])

        path.write_bytes(b'{"type":"broken"}\nnot-json\n')
        with self.assertRaises(json.JSONDecodeError):
            list(MODULE.load_records(path))

    def test_aborted_turn_is_terminal_and_claims_the_pending_user_prompt(self) -> None:
        records = [
            {"timestamp": "2026-09-20T00:00:00.000Z", "type": "response_item", "payload": {
                "type": "message", "role": "user", "content": [{"type": "input_text", "text": "Inspect the current rollout"}],
            }},
            {"timestamp": "2026-09-20T00:00:01.000Z", "type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-aborted"}},
            {"timestamp": "2026-09-20T00:00:02.000Z", "type": "event_msg", "payload": {"type": "token_count", "info": {
                "last_token_usage": {"input_tokens": 20, "output_tokens": 3, "total_tokens": 23},
                "total_token_usage": {"input_tokens": 20, "output_tokens": 3, "total_tokens": 23},
            }}},
            {"timestamp": "2026-09-20T00:00:03.000Z", "type": "event_msg", "payload": {"type": "turn_aborted", "turn_id": "turn-aborted"}},
        ]
        turns, _ = MODULE.parse_usage(self.write_rollout(records), include_prompt=True)
        self.assertEqual(turns[0]["status"], "aborted")
        self.assertEqual(turns[0]["prompt"], "Inspect the current rollout")

    def test_user_message_event_is_associated_with_the_following_turn(self) -> None:
        records = [
            {"timestamp": "2026-09-20T00:00:00.000Z", "type": "event_msg", "payload": {
                "type": "user_message", "message": "Show token totals",
            }},
            {"timestamp": "2026-09-20T00:00:01.000Z", "type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-event"}},
            {"timestamp": "2026-09-20T00:00:02.000Z", "type": "event_msg", "payload": {"type": "token_count", "info": {
                "last_token_usage": {"input_tokens": 12, "output_tokens": 2, "total_tokens": 14},
                "total_token_usage": {"input_tokens": 12, "output_tokens": 2, "total_tokens": 14},
            }}},
        ]
        turns, _ = MODULE.parse_usage(self.write_rollout(records), include_prompt=True)
        self.assertEqual(turns[0]["prompt"], "Show token totals")

    def test_post_start_user_messages_attach_to_the_active_turn_without_duplicates(self) -> None:
        records = [
            {"timestamp": "2026-09-20T00:00:00.000Z", "type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-active"}},
            {"timestamp": "2026-09-20T00:00:01.000Z", "type": "response_item", "payload": {
                "type": "message", "role": "user", "content": [{"type": "input_text", "text": "Inspect after start"}],
            }},
            {"timestamp": "2026-09-20T00:00:02.000Z", "type": "event_msg", "payload": {"type": "user_message", "message": "Inspect after start"}},
            {"timestamp": "2026-09-20T00:00:03.000Z", "type": "event_msg", "payload": {"type": "token_count", "info": {
                "last_token_usage": {"input_tokens": 8, "output_tokens": 1, "total_tokens": 9},
                "total_token_usage": {"input_tokens": 8, "output_tokens": 1, "total_tokens": 9},
            }}},
        ]
        turns, calls = MODULE.parse_usage(self.write_rollout(records), include_prompt=True)
        self.assertEqual(turns[0]["prompt"], "Inspect after start")
        self.assertEqual(calls[0]["prompt"], "Inspect after start")

    def test_started_turn_exposes_prompt_before_first_token_count(self) -> None:
        records = [
            {"timestamp": "2026-09-20T00:00:00.000Z", "type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-new"}},
            {"timestamp": "2026-09-20T00:00:01.000Z", "type": "event_msg", "payload": {"type": "user_message", "message": "Prompt before usage"}},
        ]
        turns, calls = MODULE.parse_usage(self.write_rollout(records), include_prompt=True)
        self.assertEqual(calls, [])
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]["prompt"], "Prompt before usage")
        self.assertEqual(turns[0]["status"], "in_progress")
        self.assertEqual(turns[0]["total_tokens"], 0)

    def test_multiline_prompt_is_flattened_and_deduplicated(self) -> None:
        records = [
            {"timestamp": "2026-09-20T00:00:00.000Z", "type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-multiline"}},
            {"timestamp": "2026-09-20T00:00:01.000Z", "type": "response_item", "payload": {
                "type": "message", "role": "user", "content": [{"type": "input_text", "text": "First line\nSecond line"}],
            }},
            {"timestamp": "2026-09-20T00:00:02.000Z", "type": "event_msg", "payload": {
                "type": "user_message", "message": "First line\r\nSecond line",
            }},
            {"timestamp": "2026-09-20T00:00:03.000Z", "type": "event_msg", "payload": {"type": "token_count", "info": {
                "last_token_usage": {"input_tokens": 3, "output_tokens": 1, "total_tokens": 4},
                "total_token_usage": {"input_tokens": 3, "output_tokens": 1, "total_tokens": 4},
            }}},
        ]
        turns, calls = MODULE.parse_usage(self.write_rollout(records), include_prompt=True)
        self.assertEqual(turns[0]["prompt"], "First line Second line")
        self.assertEqual(calls[0]["prompt"], "First line Second line")

    def test_csv_serialization_uses_translation_safe_line_endings(self) -> None:
        rendered = MODULE.serialize([{"turn": 1, "status": "complete", "total_tokens": 9}], "csv", "turn")
        self.assertNotIn("\r\n", rendered)
        self.assertEqual(rendered.count("\n"), 2)

    def test_latest_session_requires_explicit_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sessions = root / "sessions"
            sessions.mkdir()
            rollout = sessions / "rollout-latest.jsonl"
            rollout.write_text("{}\n", encoding="utf-8")
            args = argparse.Namespace(session=None, thread_id=None, latest=False, codex_home=str(root))
            with self.assertRaisesRegex(ValueError, "explicit --latest"):
                MODULE.resolve_session(args)
            args.latest = True
            self.assertEqual(MODULE.resolve_session(args), rollout)

    def test_watch_rejects_structured_stdout_but_allows_atomic_output(self) -> None:
        common = ["inspect_token_usage.py", "--session", str(self.write_rollout([])), "--watch", "1", "--format", "json"]
        with patch.object(MODULE.sys, "argv", common):
            self.assertEqual(MODULE.main(), 2)

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "usage.json"
            with patch.object(MODULE.sys, "argv", [*common, "--output", str(output)]), patch.object(MODULE, "write_snapshot", side_effect=KeyboardInterrupt):
                self.assertEqual(MODULE.main(), 0)

    def test_output_cannot_replace_the_selected_rollout(self) -> None:
        rollout = self.write_rollout([])
        original = rollout.read_bytes()
        with patch.object(MODULE.sys, "argv", [
            "inspect_token_usage.py", "--session", str(rollout), "--output", str(rollout),
        ]):
            self.assertEqual(MODULE.main(), 2)
        self.assertEqual(rollout.read_bytes(), original)

    def test_list_sessions_honors_csv_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sessions = root / "sessions"
            sessions.mkdir()
            (sessions / "rollout-2026-09-20-task-id.jsonl").write_text("{}\n", encoding="utf-8")
            output = root / "sessions.csv"
            args = argparse.Namespace(
                codex_home=str(root), limit=20, include_prompt=False,
                format="csv", output=str(output),
            )
            MODULE.list_local_sessions(args)
            rendered = output.read_text(encoding="utf-8")
            self.assertTrue(rendered.startswith("modified_local,task_id,path\n"))
            self.assertIn("rollout-2026-09-20-task-id.jsonl", rendered)
            self.assertEqual(list(root.glob(".sessions.csv.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
