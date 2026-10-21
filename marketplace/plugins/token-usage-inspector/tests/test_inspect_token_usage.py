from __future__ import annotations

import json
import csv
import io
import os
import subprocess
import sys
import tempfile
import time
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

    def run_json(self, *arguments, env=None):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--codex-home", str(self.home), *arguments, "--format", "json"],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_historical_output_rejects_every_selected_rollout_alias(self):
        for selector in (("--all-sessions",), ("--project", "/work/project"), ("--thread-id", "archive-task", "--historical")):
            for alias in ("same", "symlink", "hardlink"):
                with self.subTest(selector=selector, alias=alias):
                    rollout = self.write("archived_sessions/rollout-archive-task.jsonl", [
                        meta("archive-task", "/work/project"), native("2026-07-01T01:00:00Z", 40, "response"),
                    ])
                    output = self.home / f"{alias}-report.json"
                    output.unlink(missing_ok=True)
                    if alias == "same":
                        output = rollout
                    elif alias == "symlink":
                        output.symlink_to(rollout)
                    else:
                        os.link(rollout, output)
                    original = rollout.read_bytes()
                    result = subprocess.run([
                        sys.executable, str(SCRIPT), "--codex-home", str(self.home),
                        *selector, "--format", "json", "--output", str(output),
                    ], text=True, capture_output=True)
                    self.assertEqual(rollout.read_bytes(), original, result.stderr)
                    self.assertEqual(output.read_bytes(), original, result.stderr)
                    self.assertEqual(result.returncode, 2, result.stdout)
                    self.assertIn("alias", result.stderr)

    def test_project_listing_writes_each_format_to_output(self):
        self.write("sessions/rollout-project.jsonl", [meta("task", "/work/project")])
        for output_format in ("json", "csv", "table"):
            with self.subTest(format=output_format):
                output = self.home / f"projects.{output_format}"
                result = subprocess.run([
                    sys.executable, str(SCRIPT), "--codex-home", str(self.home), "--list-projects",
                    "--format", output_format, "--output", str(output),
                ], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(output.is_file(), result.stdout)
                self.assertEqual(result.stdout, "")
                rendered = output.read_text(encoding="utf-8")
                if output_format == "json":
                    rows = json.loads(rendered)
                elif output_format == "csv":
                    rows = list(csv.DictReader(io.StringIO(rendered)))
                else:
                    self.assertIn("/work/project", rendered)
                    continue
                self.assertEqual(rows[0]["project"], "/work/project")
                self.assertEqual(int(rows[0]["tasks"]), 1)

    def test_project_listing_cannot_overwrite_rollouts(self):
        rollout = self.write("sessions/rollout-project.jsonl", [meta("task", "/work/project")])
        original = rollout.read_bytes()
        result = subprocess.run([
            sys.executable, str(SCRIPT), "--codex-home", str(self.home), "--list-projects",
            "--output", str(rollout),
        ], text=True, capture_output=True)
        self.assertEqual(rollout.read_bytes(), original)
        self.assertEqual(result.returncode, 2)

    def test_native_response_identity_uses_task_and_response_not_timestamp(self):
        self.write("sessions/rollout-original.jsonl", [
            meta("task-a", "/work/project"), native("2026-07-01T01:00:00Z", 40, "response"),
        ])
        self.write("archived_sessions/rollout-copy.jsonl", [
            meta("task-a", "/work/project"), native("2026-07-02T01:00:00Z", 40, "response"),
        ])
        self.write("sessions/rollout-other-task.jsonl", [
            meta("task-b", "/work/project"), native("2026-07-01T01:00:00Z", 40, "response"),
        ])
        rows = self.run_json("--all-sessions", "--group-by", "task")
        self.assertEqual({row["task"]: (row["total_tokens"], row["usage_records"]) for row in rows}, {
            "task-a": (40, 1), "task-b": (40, 1),
        })

    def test_missing_response_ids_keep_a_task_scoped_fallback(self):
        records = [meta("task-a", "/work/project"),
                   native("2026-07-01T01:00:00Z", 40, ""), native("2026-07-02T01:00:00Z", 40, "")]
        self.write("sessions/rollout-no-id.jsonl", records)
        self.write("archived_sessions/rollout-no-id-copy.jsonl", records)
        self.write("sessions/rollout-other-task.jsonl", [
            meta("task-b", "/work/project"), native("2026-07-01T01:00:00Z", 40, ""),
        ])
        rows = self.run_json("--all-sessions", "--group-by", "task")
        self.assertEqual({row["task"]: row["total_tokens"] for row in rows}, {"task-a": 80, "task-b": 40})

    def test_recursive_filesystem_root_includes_children(self):
        root = Path(self.temp.name).anchor
        project = str(Path(root) / "work" / "project")
        self.write("sessions/rollout-root-child.jsonl", [meta("task", project), native("2026-07-01T01:00:00Z", 40, "r")])
        self.assertEqual(self.run_json("--project", root), [])
        rows = self.run_json("--project", root, "--include-subdirs")
        self.assertEqual(rows[0]["total_tokens"], 40)

    @unittest.skipUnless(hasattr(time, "tzset"), "requires system TZ support")
    def test_local_timezone_uses_each_dates_dst_rules_and_boundaries(self):
        self.write("sessions/rollout-seasons.jsonl", [
            meta("task", "/work/project"),
            native("2026-01-01T04:30:00Z", 20, "winter"),
            native("2026-07-01T04:30:00Z", 30, "summer"),
        ])
        env = {**os.environ, "TZ": "America/New_York"}
        rows = self.run_json("--all-sessions", "--group-by", "day", env=env)
        self.assertEqual({row["day"]: row["total_tokens"] for row in rows}, {"2025-12-31": 20, "2026-07-01": 30})
        for day, total in (("2025-12-31", 20), ("2026-07-01", 30)):
            with self.subTest(day=day):
                rows = self.run_json("--all-sessions", "--from", day, "--to", day, env=env)
                self.assertEqual(sum(row["total_tokens"] for row in rows), total)

    @unittest.skipUnless(hasattr(time, "tzset"), "requires system TZ support")
    def test_local_date_end_tracks_dst_changes_before_converting_to_an_offset(self):
        self.write("sessions/rollout-dst-boundaries.jsonl", [
            meta("task", "/work/project"),
            native("2026-03-09T03:59:59Z", 20, "spring-inside"),
            native("2026-03-09T04:00:00Z", 30, "spring-outside"),
            native("2026-11-02T04:59:59Z", 40, "fall-inside"),
            native("2026-11-02T05:00:00Z", 50, "fall-outside"),
        ])
        env = {**os.environ, "TZ": "America/New_York"}
        for day, total in (("2026-03-08", 20), ("2026-11-01", 40)):
            with self.subTest(day=day):
                for start in (day, f"{day}T00:00:00"):
                    rows = self.run_json("--all-sessions", "--from", start, "--to", day, env=env)
                    self.assertEqual(sum(row["total_tokens"] for row in rows), total)

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
