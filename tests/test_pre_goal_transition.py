import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from test_audit_memory_store import AuditMemoryStoreTests
from tools.pre_goal_transition import main


class PreGoalTransitionTests(unittest.TestCase):
    def _write_valid_store(self, data_dir: Path) -> None:
        helper = AuditMemoryStoreTests()
        helper._write_valid_store(data_dir)
        inventory_text = """- id: test.inventory
  status: active
  kind: semantic
  summary: Temporary inventory entry for goal-transition tests.
  source: inventory.yaml
  last_verified: 2026-05-25
  retrieval_cue: Used to satisfy inventory validation in test fixtures.
"""
        (data_dir / "inventory.yaml").write_text(inventory_text, encoding="utf-8")

    def _base_args(self, data_dir: Path) -> list[str]:
        return [
            str(data_dir),
            "--new-day",
            "420",
            "--new-goal",
            "Ship transition-safe memory updates",
            "--source-summary",
            "Visible event states new cycle starts on day-420.",
        ]

    @patch("tools.pre_goal_transition.subprocess.run")
    def test_success_ready_clean_git(self, mock_run):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(self._base_args(data_dir))
            out = buf.getvalue()
            self.assertEqual(0, rc)
            self.assertIn("PRE-GOAL-TRANSITION CHECK", out)
            self.assertIn("Current day: 419", out)
            self.assertIn("Repo head: abc123", out)
            self.assertIn("Repo status: clean", out)
            self.assertIn("Audit status: OK", out)
            self.assertIn("Inventory status: OK", out)
            self.assertIn(
                "READY: apply the transition from visible-event text, then re-check public_comms and visible events before any announcement.",
                out,
            )

    @patch("tools.pre_goal_transition.subprocess.run")
    def test_blocked_blank_goal(self, mock_run):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            args = self._base_args(data_dir)
            args[args.index("--new-goal") + 1] = "   "
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(args)
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("BLOCKED:", out)
            self.assertIn("--new-goal must not be blank", out)

    @patch("tools.pre_goal_transition.subprocess.run")
    def test_blocked_blank_source_summary(self, mock_run):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            args = self._base_args(data_dir)
            args[args.index("--source-summary") + 1] = "  "
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(args)
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("BLOCKED:", out)
            self.assertIn("--source-summary must not be blank", out)

    @patch("tools.pre_goal_transition.subprocess.run")
    def test_blocked_dirty_repo(self, mock_run):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": " M tools/pre_goal_transition.py\n"})(),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(self._base_args(data_dir))
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("Repo status: dirty", out)
            self.assertIn("repo has uncommitted changes", out)

    @patch("tools.pre_goal_transition.audit_store")
    @patch("tools.pre_goal_transition.subprocess.run")
    def test_blocked_audit_errors(self, mock_run, mock_audit_store):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        mock_audit_store.return_value = (["missing key"], [])
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(self._base_args(data_dir))
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("Audit status: errors", out)
            self.assertIn("memory-store audit has errors", out)

    @patch("tools.pre_goal_transition.subprocess.run")
    def test_blocked_when_new_day_lower_than_current(self, mock_run):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            args = self._base_args(data_dir)
            args[args.index("--new-day") + 1] = "418"
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(args)
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("Current day: 419", out)
            self.assertIn("--new-day must not be lower than current parsed day", out)

    @patch("tools.pre_goal_transition.load_inventory")
    @patch("tools.pre_goal_transition.subprocess.run")
    def test_blocked_unreadable_inventory(self, mock_run, mock_load_inventory):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        mock_load_inventory.side_effect = OSError("read failed")
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(self._base_args(data_dir))
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("Inventory status: unreadable", out)
            self.assertIn("inventory is unreadable", out)

    @patch("tools.pre_goal_transition.validate_inventory")
    @patch("tools.pre_goal_transition.load_inventory")
    @patch("tools.pre_goal_transition.subprocess.run")
    def test_blocked_invalid_inventory(self, mock_run, mock_load_inventory, mock_validate_inventory):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        mock_load_inventory.return_value = []
        mock_validate_inventory.return_value = ["missing field"]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(self._base_args(data_dir))
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("Inventory status: invalid", out)
            self.assertIn("inventory is invalid", out)

    @patch("tools.pre_goal_transition.subprocess.run")
    def test_optional_unchanged_room_reported(self, mock_run):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(self._base_args(data_dir))
            out = buf.getvalue()
            self.assertEqual(0, rc)
            self.assertIn("Proposed new room: (unchanged)", out)


if __name__ == "__main__":
    unittest.main()
