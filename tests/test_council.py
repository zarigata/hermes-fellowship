import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import council


FAKE_HERMES = '''#!/usr/bin/env python3
import json, sys, time, os
prompt = sys.stdin.read()
if "TEST_TIMEOUT" in prompt:
    time.sleep(30)
if "TEST_MISSING_RESULT" in prompt:
    print(json.dumps({"type": "text", "text": "still working"}))
elif "TEST_FAILED_RESULT" in prompt:
    print(json.dumps({"type": "result", "exit_code": 1, "text": "failed"}))
else:
    print("diagnostic non-JSON line")
    print(json.dumps({"type": "result", "exit_code": 0, "text": prompt,
                      "argv": sys.argv[1:], "cwd": os.getcwd(),
                      "worker": os.environ.get("FELLOWSHIP_WORKER"),
                      "hermes_home_present": "HERMES_HOME" in os.environ}))
'''


class CouncilTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.state = self.base / "hermes-state"
        self.workspace = self.base / "project with spaces"
        self.workspace.mkdir()
        self.fake = self.base / "fake-hermes"
        self.fake.write_text(FAKE_HERMES)
        self.fake.chmod(0o700)
        self.task_path = self.base / "task.json"
        self.write_task()

    def write_task(self, goal="Review repository"):
        self.task_path.write_text(json.dumps({"goal": goal, "context": "Use the fixture workspace.",
                                             "acceptance": ["Return evidence"],
                                             "authorized_actions": ["Read files"]}))

    def setup_profile(self, agent="dragonborn"):
        pack = self.state / "profiles" / council.profile_name(agent) / "fellowship"
        pack.mkdir(parents=True)
        (pack / "council.json").write_text("{}")

    def run_fixture(self, seconds=10):
        output = io.StringIO()
        with patch.object(council, "hermes_root", return_value=self.state), \
             patch.object(council.shutil, "which", return_value=str(self.fake)), \
             patch.dict(os.environ, {"HERMES_HOME": "/active/profile"}), \
             contextlib.redirect_stdout(output):
            code = council.run_agent("dragonborn", self.workspace, self.task_path, seconds, 7)
        return code, json.loads(output.getvalue())

    def test_task_text_is_literal_and_profile_is_explicit(self):
        self.setup_profile()
        marker = self.base / "SHOULD_NOT_EXIST"
        payload = f"$(touch '{marker}') `touch '{marker}'` ; quote ' and newline\nend"
        self.write_task(payload)
        code, receipt = self.run_fixture()
        self.assertEqual(code, 0)
        self.assertEqual(receipt["status"], "completed_unreviewed")
        result = receipt["result"]
        self.assertIn(json.dumps(payload)[1:-1], result["text"])
        self.assertFalse(marker.exists())
        self.assertEqual(result["argv"][:2], ["-p", "fellowship-dragonborn"])
        self.assertEqual(result["cwd"], str(self.workspace))
        self.assertEqual(result["worker"], "dragonborn")
        self.assertFalse(result["hermes_home_present"])
        self.assertNotIn("--yolo", result["argv"])

    def test_missing_terminal_result_is_failure(self):
        self.setup_profile()
        self.write_task("TEST_MISSING_RESULT")
        code, receipt = self.run_fixture()
        self.assertEqual(code, 1)
        self.assertEqual(receipt["status"], "failed")
        self.assertIsNone(receipt["result"])

    def test_failed_result_even_with_process_zero_is_failure(self):
        self.setup_profile()
        self.write_task("TEST_FAILED_RESULT")
        code, receipt = self.run_fixture()
        self.assertEqual(code, 1)
        self.assertEqual(receipt["status"], "failed")

    def test_timeout_is_unknown_effects(self):
        self.setup_profile()
        self.write_task("TEST_TIMEOUT")
        code, receipt = self.run_fixture(seconds=1)
        self.assertEqual(code, 1)
        self.assertEqual(receipt["status"], "timeout_unknown_effects")
        self.assertLess(receipt["duration_seconds"], 10)

    def test_run_artifacts_are_private(self):
        self.setup_profile()
        _, receipt = self.run_fixture()
        run_dir = Path(receipt["run_directory"])
        self.assertEqual(run_dir.stat().st_mode & 0o777, 0o700)
        for name in ("events.jsonl", "stderr.log", "receipt.json"):
            self.assertEqual((run_dir / name).stat().st_mode & 0o777, 0o600)

    def test_profile_lock_rejects_competing_launcher(self):
        with council.lock_profile(self.state, "same"):
            with self.assertRaisesRegex(ValueError, "busy"):
                with council.lock_profile(self.state, "same"):
                    self.fail("Lock should reject second holder")
        with council.lock_profile(self.state, "same"):
            pass

    def test_nested_launch_rejected(self):
        with patch.dict(os.environ, {"FELLOWSHIP_WORKER": "sauron"}):
            with self.assertRaisesRegex(ValueError, "Nested"):
                council.run_agent("dragonborn", self.workspace, self.task_path)

    def test_coordinator_requires_interactive_start(self):
        with self.assertRaisesRegex(ValueError, "interactively"):
            council.run_agent("gandalf", self.workspace, self.task_path)

    def test_invalid_task_rejected(self):
        for task in ({"goal": "x"}, {"goal": "x", "context": "x", "acceptance": [], "authorized_actions": ["read"]},
                     {"goal": "x", "context": "x", "acceptance": ["ok"], "authorized_actions": ["read"], "command": "bad"}):
            self.task_path.write_text(json.dumps(task))
            with self.assertRaises(ValueError):
                council.load_task(self.task_path)

    def test_bounds_rejected(self):
        with self.assertRaises(ValueError):
            council.build_command("hermes", "dragonborn", 0)
        with self.assertRaises(ValueError):
            council.run_agent("dragonborn", self.workspace, self.task_path, seconds=0)

    def test_missing_profile_rejected(self):
        with patch.object(council, "hermes_root", return_value=self.state), \
             patch.object(council.shutil, "which", return_value=str(self.fake)):
            with self.assertRaisesRegex(ValueError, "not installed"):
                council.run_agent("dragonborn", self.workspace, self.task_path)

    def test_standard_profile_root_resolution(self):
        with patch.object(Path, "home", return_value=self.base):
            base = self.base / ".hermes"
            with patch.dict(os.environ, {"HERMES_HOME": str(base / "profiles" / "fellowship-gandalf")}):
                self.assertEqual(council.hermes_root(), base)
            with patch.dict(os.environ, {"HERMES_HOME": "/unrelated/custom/root"}):
                with self.assertRaisesRegex(ValueError, "unsupported"):
                    council.hermes_root()

    def test_install_preview_does_not_write(self):
        with patch.object(council, "hermes_root", return_value=self.state), contextlib.redirect_stdout(io.StringIO()):
            council.install(False)
        self.assertFalse(self.state.exists())

    def test_install_creates_profiles_and_preserves_existing_on_retry(self):
        calls = []

        def fake_command(cmd, **kwargs):
            calls.append(cmd)
            if cmd[1:3] == ["profile", "create"]:
                path = self.state / "profiles" / cmd[3]
                path.mkdir(parents=True)
                (path / "config.yaml").write_text("{}\n")

        with patch.object(council, "hermes_root", return_value=self.state), \
             patch.object(council.shutil, "which", return_value=str(self.fake)), \
             patch.object(council.subprocess, "run", side_effect=fake_command), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(council.install(True), 0)
            self.assertEqual(len(list((self.state / "profiles").iterdir())), 7)
            soul = self.state / "profiles" / "fellowship-gandalf" / "SOUL.md"
            self.assertNotIn("{{PACK_ROOT}}", soul.read_text())
            self.assertIn(str(soul.parent / "fellowship"), soul.read_text())
            original = soul.read_bytes()
            count = len(calls)
            with self.assertRaisesRegex(ValueError, "overwrite"):
                council.install(True)
            self.assertEqual(len(calls), count)
            self.assertEqual(soul.read_bytes(), original)
            self.assertFalse(any("--clone" in cmd or "--clone-all" in cmd for cmd in calls))


if __name__ == "__main__":
    unittest.main()
