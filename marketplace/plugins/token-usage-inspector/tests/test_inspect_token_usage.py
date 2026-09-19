from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "skills/token-usage-inspector/scripts/inspect_token_usage.py"
if not SCRIPT.exists():
    SCRIPT = ROOT / "marketplace/plugins/token-usage-inspector/skills/token-usage-inspector/scripts/inspect_token_usage.py"


def meta(task: str, project: str, source="cli"):
    return {
        "timestamp": "2026-07-01T00:00:00Z",
        "type": "session_meta",
        "payload": {"id": task, "timestamp": "2026-07-01T00:00:00Z", "cwd": project, "source": source},
    }


def context(model: str):
    return {"timestamp": "2026-07-01T00:00:01Z", "type": "turn_context", "payload": {"model": model}}


def usage(total: int):
    return {
        "input_tokens": total - 10,
        "cached_input_tokens": max(total - 20, 0),
        "output_tokens": 10,
        "reasoning_output_tokens": 3,
        "total_tokens": total,
    }


def legacy(stamp: str, total: int, last: int = 0):
    return {
        "timestamp": stamp,
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "info": {"total_token_usage": usage(total), "last_token_usage": usage(last) if last else {}},
        },
    }


def native(stamp: str, total: int, response_id: str):
    return {
        "timestamp": stamp,
        "type": "token_usage_record",
        "payload": {"turn_id": "turn", "response_id": response_id, "usage": usage(total)},
    }


class HistoricalUsageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative: str, records):
        path = self.home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
        return path

    def run_json(self, *arguments):
        result = subprocess.run(
            ["python3", str(SCRIPT), "--codex-home", str(self.home), *arguments, "--format", "json"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_combines_legacy_and_native_files_and_deduplicates_archive(self):
        task = "00000000-0000-0000-0000-000000000001"
        project = "/work/project"
        old = [meta(task, project), context("gpt-old"), legacy("2026-07-01T01:00:00Z", 100), legacy("2026-07-01T01:01:00Z", 150)]
        new = [meta(task, project), context("gpt-new"), native("2026-07-02T01:00:00Z", 40, "resp-1")]
        self.write("sessions/2026/07/01/rollout-old.jsonl", old)
        self.write("sessions/2026/07/02/rollout-new.jsonl", new)
        self.write("archived_sessions/rollout-new-copy.jsonl", new)

        rows = self.run_json("--project", project, "--group-by", "model")
        totals = {row["model"]: row["total_tokens"] for row in rows}
        self.assertEqual(totals, {"gpt-new": 40, "gpt-old": 150})

    def test_spawned_inherited_snapshot_is_only_a_baseline(self):
        task = "00000000-0000-0000-0000-000000000002"
        project = "/work/project"
        source = {"subagent": {"thread_spawn": {"parent": "root"}}}
        records = [
            meta(task, project, source),
            context("gpt-old"),
            legacy("2026-07-03T01:00:00Z", 100),
            {"timestamp": "2026-07-03T01:00:01Z", "type": "inter_agent_communication_metadata", "payload": {}},
            legacy("2026-07-03T01:01:00Z", 150),
        ]
        self.write("sessions/2026/07/03/rollout-spawned.jsonl", records)
        rows = self.run_json("--project", project, "--group-by", "source")
        self.assertEqual(rows[0]["source"], "spawned")
        self.assertEqual(rows[0]["total_tokens"], 50)

    def test_date_end_is_inclusive_and_project_subdirs_are_opt_in(self):
        root = "/work/project"
        task_a = "00000000-0000-0000-0000-000000000003"
        task_b = "00000000-0000-0000-0000-000000000004"
        self.write(
            "sessions/2026/07/04/rollout-root.jsonl",
            [meta(task_a, root), context("gpt"), native("2026-07-04T23:59:59Z", 25, "a")],
        )
        self.write(
            "sessions/2026/07/04/rollout-child.jsonl",
            [meta(task_b, root + "/child"), context("gpt"), native("2026-07-04T12:00:00Z", 30, "b")],
        )

        exact = self.run_json("--project", root, "--from", "2026-07-04", "--to", "2026-07-04", "--timezone", "UTC", "--group-by", "day")
        self.assertEqual(exact[0]["total_tokens"], 25)
        recursive = self.run_json("--project", root, "--include-subdirs", "--to", "2026-07-04", "--timezone", "UTC", "--group-by", "day")
        self.assertEqual(recursive[0]["total_tokens"], 55)


if __name__ == "__main__":
    unittest.main()
