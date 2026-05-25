import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from test_audit_memory_store import AuditMemoryStoreTests
from tools.prepare_consolidation import main


class PrepareConsolidationTests(unittest.TestCase):
    def _write_valid_store(self, data_dir: Path) -> None:
        helper = AuditMemoryStoreTests()
        helper._write_valid_store(data_dir)

    @patch("tools.pre_consolidate.subprocess.run")
    def test_success_writes_candidate_and_reports_ready(self, mock_run):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            candidate = data_dir / "candidate.txt"

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--next-session-goal",
                        "Ship practical memory improvements",
                        "--next-short-goal",
                        "Audit loops and confirm top priority",
                        "--candidate-path",
                        str(candidate),
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(0, rc)
            self.assertTrue(candidate.exists())
            self.assertIn("PREPARE-CONSOLIDATION", out)
            self.assertIn(f"Candidate path: {candidate.resolve()}", out)
            self.assertIn("Candidate total chars: ", out)
            self.assertIn("Candidate embedded CHAR_COUNT: ", out)
            self.assertIn(
                "READY: review rendered lean memory and visible events before consolidating.",
                out,
            )

    @patch("tools.pre_consolidate.subprocess.run")
    def test_fails_when_candidate_path_is_directory(self, mock_run):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            candidate_dir = data_dir / "not-a-file"
            candidate_dir.mkdir()

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--next-session-goal",
                        "Ship practical memory improvements",
                        "--next-short-goal",
                        "Audit loops and confirm top priority",
                        "--candidate-path",
                        str(candidate_dir),
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("ERROR: unable to write candidate file:", out)

    @patch("tools.prepare_consolidation.render_lean_memory")
    @patch("tools.pre_consolidate.subprocess.run")
    def test_blocks_when_generated_candidate_misses_required_cue(self, mock_run, mock_render):
        mock_run.side_effect = [
            type("CP", (), {"returncode": 0, "stdout": "abc123\n"})(),
            type("CP", (), {"returncode": 0, "stdout": ""})(),
        ]
        body = "Day / goal anchor\nDay 419\nGoal: Improve your memory\nRoom: #rest\n"
        mock_render.return_value = f"{body}CHAR_COUNT={len(body)}\n"

        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            candidate = data_dir / "candidate.txt"

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--next-session-goal",
                        "Ship practical memory improvements",
                        "--next-short-goal",
                        "Audit loops and confirm top priority",
                        "--candidate-path",
                        str(candidate),
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("- Candidate cue status: WARN", out)
            self.assertIn("BLOCKED: candidate missing required cues or do_not_repeat topics", out)


if __name__ == "__main__":
    unittest.main()
