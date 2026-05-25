import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from test_audit_memory_store import AuditMemoryStoreTests
from tools.pre_consolidate import main


class PreConsolidateTests(unittest.TestCase):
    def _write_valid_store(self, data_dir: Path) -> None:
        helper = AuditMemoryStoreTests()
        helper._write_valid_store(data_dir)

    def _write_candidate(self, path: Path, include_email: bool = True) -> None:
        lines = [
            "day 419",
            "goal: improve your memory",
            "room: #rest",
        ]
        if include_email:
            lines.append("email: a@example.com")
        path.write_text("\n".join(lines), encoding="utf-8")

    @patch("tools.pre_consolidate.subprocess.run")
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
                rc = main(
                    [
                        str(data_dir),
                        "--next-session-goal",
                        "Ship practical memory improvements",
                        "--next-short-goal",
                        "Audit loops and confirm top priority",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(0, rc)
            self.assertIn("PRE-CONSOLIDATE CHECK", out)
            self.assertIn("Repo head: abc123", out)
            self.assertIn("Repo status: clean", out)
            self.assertIn("Audit status: OK", out)
            self.assertIn(
                "READY: review rendered lean memory and visible events before consolidating.",
                out,
            )

    @patch("tools.pre_consolidate.subprocess.run")
    def test_blocked_blank_goal_field(self, mock_run):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--next-session-goal",
                        "   ",
                        "--next-short-goal",
                        "Audit loops and confirm top priority",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("BLOCKED:", out)
            self.assertIn("--next-session-goal must not be blank", out)

    @patch("tools.pre_consolidate.subprocess.run")
    def test_blocked_too_many_words_short_goal(self, mock_run):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--next-session-goal",
                        "Ship practical memory improvements",
                        "--next-short-goal",
                        "one two three four five six seven eight nine ten eleven",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("--next-short-goal must be 10 words or fewer", out)

    @patch("tools.pre_consolidate.subprocess.run")
    def test_blocked_dirty_repo(self, mock_run):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": " M tools/pre_consolidate.py\n"})(),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--next-session-goal",
                        "Ship practical memory improvements",
                        "--next-short-goal",
                        "Audit loops and confirm top priority",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("Repo status: dirty", out)
            self.assertIn("repo has uncommitted changes", out)

    @patch("tools.pre_consolidate.audit_store")
    @patch("tools.pre_consolidate.subprocess.run")
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
                rc = main(
                    [
                        str(data_dir),
                        "--next-session-goal",
                        "Ship practical memory improvements",
                        "--next-short-goal",
                        "Audit loops and confirm top priority",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("Audit status: errors", out)
            self.assertIn("memory-store audit has errors", out)

    @patch("tools.pre_consolidate.subprocess.run")
    def test_success_with_valid_candidate(self, mock_run):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            candidate = data_dir / "candidate.txt"
            self._write_candidate(candidate, include_email=True)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--next-session-goal",
                        "Ship practical memory improvements",
                        "--next-short-goal",
                        "Audit loops and confirm top priority",
                        "--candidate",
                        str(candidate),
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(0, rc)
            self.assertIn("Candidate check:", out)
            self.assertIn(f"- Path: {candidate.resolve()}", out)
            self.assertIn("- Candidate cue status: OK", out)
            self.assertIn(
                "READY: review rendered lean memory and visible events before consolidating.",
                out,
            )

    @patch("tools.pre_consolidate.subprocess.run")
    def test_blocked_when_candidate_missing_required_cue(self, mock_run):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            candidate = data_dir / "candidate.txt"
            self._write_candidate(candidate, include_email=False)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--next-session-goal",
                        "Ship practical memory improvements",
                        "--next-short-goal",
                        "Audit loops and confirm top priority",
                        "--candidate",
                        str(candidate),
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("- Candidate cue status: WARN", out)
            self.assertIn("candidate missing required cues or do_not_repeat topics", out)


if __name__ == "__main__":
    unittest.main()
