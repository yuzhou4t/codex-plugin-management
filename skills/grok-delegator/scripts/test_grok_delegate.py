#!/usr/bin/env python3
"""Behavioral tests for the portable Grok adapter using a fake CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


SCRIPT = Path(__file__).with_name("grok_delegate.py")
SESSION = "11111111-2222-4333-8444-555555555555"


class GrokDelegateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="grok-delegator-test-")
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.fake = self.root / ("grok.exe" if os.name == "nt" else "grok")
        self.arguments_log = self.root / "arguments.json"
        self.mode_file = self.root / "fake-mode.txt"
        self.fake.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import json, os, pathlib, sys
                args = sys.argv[1:]
                if '--version' in args:
                    print('grok 9.9.9-test')
                    raise SystemExit(0)
                if '--help' in args:
                    print('--prompt-file --cwd --sandbox --permission-mode --tools --allow --deny --resume')
                    raise SystemExit(0)
                pathlib.Path({str(self.arguments_log)!r}).write_text(json.dumps(args), encoding='utf-8')
                cwd = pathlib.Path(args[args.index('--cwd') + 1])
                mode_path = pathlib.Path({str(self.mode_file)!r})
                mode = mode_path.read_text(encoding='utf-8') if mode_path.exists() else 'success'
                if mode == 'success':
                    (cwd / 'out.txt').write_text('implemented\\n', encoding='utf-8')
                elif mode == 'violation':
                    (cwd / 'outside.txt').write_text('bad\\n', encoding='utf-8')
                elif mode == 'resume':
                    (cwd / 'out.txt').write_text('fixed\\n', encoding='utf-8')
                elif mode == 'workspace':
                    (cwd / 'src').mkdir(exist_ok=True)
                    (cwd / 'src' / 'created.txt').write_text('workspace write\\n', encoding='utf-8')
                print(json.dumps({{'type':'text','data':'Done. Source: https://example.com/source'}}))
                print(json.dumps({{'type':'tool_call','toolCallId':'null-output','toolName':'ReadFile','status':'in_progress'}}))
                print(json.dumps({{'type':'tool_call_update','toolCallId':'null-output','status':'completed','rawOutput':None}}))
                print(json.dumps({{'type':'end','stopReason':'end_turn','sessionId':'{SESSION}','modelUsage':{{'grok-test':{{}}}},'usage':{{'input_tokens':1}}}}))
                """
            ),
            encoding="utf-8",
        )
        self.fake.chmod(0o755)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def task(self, **changes: object) -> Path:
        value: dict[str, object] = {
            "id": "test-task",
            "mode": "engineering",
            "cwd": str(self.workspace),
            "goal": "Create out.txt",
            "allowed_paths": ["out.txt"],
            "allowed_commands": [],
            "checks": [[sys.executable, "-c", "from pathlib import Path; assert Path('out.txt').read_text() in {'implemented\\n','fixed\\n'}"]],
            "acceptance": ["out.txt exists with expected content"],
            "timeout_seconds": 60,
        }
        value.update(changes)
        path = self.root / "task.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def run_cli(self, *arguments: str, mode: str = "success") -> subprocess.CompletedProcess[str]:
        self.mode_file.write_text(mode, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--grok-bin", str(self.fake), *arguments],
            capture_output=True,
            text=True,
            env=os.environ,
            timeout=30,
            check=False,
        )

    def test_engineering_run_is_scoped_and_requires_codex_review(self) -> None:
        receipt = self.root / "receipt.json"
        result = self.run_cli("run", "--task", str(self.task()), "--receipt", str(receipt))
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "needs_code_review")
        self.assertEqual(output["changed_paths"], ["out.txt"])
        self.assertEqual(output["scope_violations"], [])
        self.assertEqual(output["checks"][0]["exit_code"], 0)
        invoked = json.loads(self.arguments_log.read_text(encoding="utf-8"))
        self.assertIn("workspace", invoked)
        self.assertIn("dontAsk", invoked)
        self.assertNotIn("--always-approve", invoked)
        self.assertNotIn("bypassPermissions", invoked)
        self.assertIn("--no-subagents", invoked)
        self.assertIn("--no-plan", invoked)

    def test_scope_violation_cannot_be_accepted(self) -> None:
        receipt = self.root / "receipt.json"
        result = self.run_cli("run", "--task", str(self.task()), "--receipt", str(receipt), mode="violation")
        self.assertEqual(result.returncode, 2)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "scope_violation")
        self.assertEqual(output["scope_violations"], ["outside.txt"])
        self.assertEqual(output["checks"], [])

    def test_workspace_write_allows_normal_files_and_keeps_protected_denies(self) -> None:
        receipt = self.root / "workspace-receipt.json"
        task = self.task(
            id="workspace-task",
            workspace_write=True,
            allowed_paths=[],
            checks=[[sys.executable, "-c", "from pathlib import Path; assert Path('src/created.txt').read_text() == 'workspace write\\n'"]],
            acceptance=["Normal workspace file is created"],
        )
        result = self.run_cli("run", "--task", str(task), "--receipt", str(receipt), mode="workspace")
        self.assertEqual(result.returncode, 0, result.stdout)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "needs_code_review")
        self.assertEqual(output["changed_paths"], ["src/created.txt"])
        invoked = json.loads(self.arguments_log.read_text(encoding="utf-8"))
        resolved = self.workspace.resolve()
        self.assertIn(f"Edit({resolved / '**'})", invoked)
        self.assertIn(f"Write({resolved / '.git' / '**'})", invoked)

    def test_research_response_only_uses_web_without_terminal(self) -> None:
        receipt = self.root / "research-receipt.json"
        task = self.task(
            id="research-task",
            mode="research",
            allowed_paths=[],
            checks=[],
            acceptance=["Return current sources"],
            web=True,
        )
        result = self.run_cli("run", "--task", str(task), "--receipt", str(receipt), mode="response")
        self.assertEqual(result.returncode, 0, result.stdout)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "needs_source_review")
        self.assertEqual(output["sources"], ["https://example.com/source"])
        invoked = json.loads(self.arguments_log.read_text(encoding="utf-8"))
        tools = invoked[invoked.index("--tools") + 1]
        self.assertIn("web_search", tools)
        self.assertNotIn("run_terminal_command", tools)

    def test_resume_reuses_the_recorded_session(self) -> None:
        receipt = self.root / "receipt.json"
        first = self.run_cli("run", "--task", str(self.task()), "--receipt", str(receipt))
        self.assertEqual(first.returncode, 0, first.stdout)
        feedback = self.root / "feedback.txt"
        feedback.write_text("Use the corrected content.", encoding="utf-8")
        second = self.run_cli("resume", "--receipt", str(receipt), "--feedback", str(feedback), mode="resume")
        self.assertEqual(second.returncode, 0, second.stdout)
        invoked = json.loads(self.arguments_log.read_text(encoding="utf-8"))
        self.assertEqual(invoked[invoked.index("--resume") + 1], SESSION)
        saved = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(len(saved["attempts"]), 2)
        self.assertEqual(self.workspace.joinpath("out.txt").read_text(), "fixed\n")

    def test_protected_and_escaping_paths_are_rejected(self) -> None:
        for name in ("../outside.txt", ".git/config", ".env"):
            with self.subTest(name=name):
                task = self.task(allowed_paths=[name])
                result = self.run_cli("validate", "--task", str(task))
                self.assertEqual(result.returncode, 2)
                self.assertIn("path", json.loads(result.stdout)["error"])

    def test_missing_host_check_is_a_verification_failure_receipt(self) -> None:
        receipt = self.root / "missing-check-receipt.json"
        task = self.task(checks=[["definitely-not-a-real-command-for-grok-delegator"]])
        result = self.run_cli("run", "--task", str(task), "--receipt", str(receipt))
        self.assertEqual(result.returncode, 2, result.stdout)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "verification_failed")
        self.assertIsNone(output["checks"][0]["exit_code"])
        self.assertTrue(receipt.is_file())

    def test_invalid_command_container_returns_contract_error(self) -> None:
        task = self.task(allowed_commands=None)
        result = self.run_cli("validate", "--task", str(task))
        self.assertEqual(result.returncode, 2)
        self.assertIn("must be arrays", json.loads(result.stdout)["error"])


if __name__ == "__main__":
    unittest.main()
