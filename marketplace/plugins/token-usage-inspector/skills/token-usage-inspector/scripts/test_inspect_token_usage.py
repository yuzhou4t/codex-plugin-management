#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
