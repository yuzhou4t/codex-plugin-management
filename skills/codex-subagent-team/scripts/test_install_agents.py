#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
INSTALLER = SCRIPT_DIR / "install-agents.sh"
REPO = SCRIPT_DIR.parents[2]


class InstallAgentsTests(unittest.TestCase):
    def run_installer(self, codex_home: Path, user_home: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sh", str(INSTALLER)],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": str(user_home), "CODEX_HOME": str(codex_home)},
        )

    def test_installer_registers_all_roles_in_custom_codex_home_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_home = root / "home"
            codex_home = root / "custom-codex"
            user_home.mkdir()
            codex_home.mkdir()
            config = codex_home / "config.toml"
            config.write_text('model_reasoning_effort = "high"\n\n[projects."/tmp/example"]\ntrust_level = "trusted"\n', encoding="utf-8")

            first = self.run_installer(codex_home, user_home)
            self.assertEqual(first.returncode, 0, first.stderr)
            first_bytes = config.read_bytes()
            second = self.run_installer(codex_home, user_home)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(config.read_bytes(), first_bytes)

            parsed = tomllib.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(parsed["projects"]["/tmp/example"]["trust_level"], "trusted")
            for role in ("luna_patcher", "sol_executor", "terra_executor", "terra_reviewer"):
                installed = (codex_home / "agents" / f"{role}.toml").resolve()
                self.assertEqual(Path(parsed["agents"][role]["config_file"]).resolve(), installed)
                self.assertTrue(installed.is_file())

            doctor = subprocess.run(
                ["python3", str(REPO / "scripts" / "doctor.py"), "--home", str(user_home), "--skip-plugins"],
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "CODEX_HOME": str(codex_home)},
            )
            self.assertEqual(doctor.returncode, 0, doctor.stderr)
            self.assertIn("Installed managed Subagents: 4/4", doctor.stdout)
            self.assertIn("Registered managed Subagents: 4/4", doctor.stdout)
            self.assertNotIn("managed Subagent missing", doctor.stdout)
            self.assertNotIn("managed Subagent is not registered", doctor.stdout)

    def test_installer_refuses_an_unmanaged_role_collision(self) -> None:
        variants = (
            '[agents.sol_executor]\nconfig_file = "/tmp/user-owned.toml"\n',
            '[agents."sol_executor"]\nconfig_file = "/tmp/user-owned.toml"\n',
            'agents."sol_executor".config_file = "/tmp/user-owned.toml"\n',
            '[agents]\nsol_executor = { config_file = "/tmp/user-owned.toml" }\n',
        )
        for original in variants:
            with self.subTest(original=original), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                user_home = root / "home"
                codex_home = root / "custom-codex"
                user_home.mkdir()
                codex_home.mkdir()
                config = codex_home / "config.toml"
                config.write_text(original, encoding="utf-8")

                result = self.run_installer(codex_home, user_home)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("already exists outside the managed block", result.stderr)
                self.assertEqual(config.read_text(encoding="utf-8"), original)

    def test_installer_refuses_to_detach_a_symlinked_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_home = root / "home"
            codex_home = root / "custom-codex"
            user_home.mkdir()
            codex_home.mkdir()
            target = root / "managed-config.toml"
            target.write_text('model = "gpt-6-astra"\n', encoding="utf-8")
            config = codex_home / "config.toml"
            config.symlink_to(target)

            result = self.run_installer(codex_home, user_home)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Refusing to replace symlinked Codex config.toml", result.stderr)
            self.assertTrue(config.is_symlink())
            self.assertEqual(target.read_text(encoding="utf-8"), 'model = "gpt-6-astra"\n')
            self.assertFalse((codex_home / "agents").exists())

    def test_marker_text_inside_multiline_value_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_home = root / "home"
            codex_home = root / "custom-codex"
            user_home.mkdir()
            codex_home.mkdir()
            config = codex_home / "config.toml"
            instructions = (
                'developer_instructions = """Keep this text.\n'
                '# BEGIN codex-subagent-team managed roles\n'
                'This is user content, not a managed TOML comment block.\n'
                '# END codex-subagent-team managed roles\n'
                'Keep this too."""\n'
            )
            config.write_text(instructions, encoding="utf-8")

            first = self.run_installer(codex_home, user_home)
            self.assertEqual(first.returncode, 0, first.stderr)
            second = self.run_installer(codex_home, user_home)
            self.assertEqual(second.returncode, 0, second.stderr)
            installed = config.read_text(encoding="utf-8")
            self.assertIn(instructions.rstrip(), installed)
            self.assertEqual(installed.count("# BEGIN codex-subagent-team managed roles"), 2)
            self.assertEqual(tomllib.loads(installed)["developer_instructions"], tomllib.loads(instructions)["developer_instructions"])

    def test_outer_macos_installer_uses_custom_codex_home_for_skills_and_agents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_home = root / "home"
            codex_home = root / "custom-codex"
            user_home.mkdir()
            fake_codex = root / "codex"
            fake_codex.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_codex.chmod(0o755)

            result = subprocess.run(
                ["zsh", str(REPO / "scripts" / "install-macos.sh")],
                check=False,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "HOME": str(user_home),
                    "CODEX_HOME": str(codex_home),
                    "PLUGIN_MANAGER_CODEX_BIN": str(fake_codex),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((codex_home / "skills" / "codex-subagent-team" / "SKILL.md").is_file())
            self.assertTrue((codex_home / "agents" / "sol_executor.toml").is_file())
            self.assertFalse((user_home / ".codex" / "skills").exists())

    def test_powershell_installer_maintains_the_same_atomic_registration_boundary(self) -> None:
        source = (SCRIPT_DIR / "install-agents.ps1").read_text(encoding="utf-8")
        helper = (SCRIPT_DIR / "install_agents.py").read_text(encoding="utf-8")
        self.assertIn("install_agents.py", source)
        self.assertIn("--codex-home", source)
        self.assertIn("tomllib.loads", helper)
        self.assertIn("config_path.is_symlink()", helper)
        self.assertIn("os.replace(temporary, path)", helper)
        self.assertIn("already exists outside the managed block", helper)


if __name__ == "__main__":
    unittest.main()
