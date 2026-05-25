import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tools.constraint_test_report import main


class ConstraintTestReportTests(unittest.TestCase):
    def _write_store(self, data_dir: Path) -> None:
        (data_dir / "identity_constraints.json").write_text(
            json.dumps(
                {
                    "schema": "memory-kit/v1",
                    "memory_type": "identity_constraints",
                    "principles": [],
                    "hard_rules": ["Rule one", "Rule two"],
                    "anchors": {
                        "room": "#rest",
                        "contact_email": "gpt-5.4@agentvillage.org",
                        "memory_kit_path": "/home/computeruse/gpt54-memory-kit",
                    },
                    "do_not_store": [],
                }
            ),
            encoding="utf-8",
        )
        (data_dir / "active_frontier.json").write_text(
            json.dumps(
                {
                    "schema": "memory-kit/v1",
                    "memory_type": "active_frontier",
                    "focus": {"context": "day-419 memory-improvement cycle", "goal": "Improve your memory"},
                    "tasks": [],
                    "high_priority_do_not_repeat": [],
                }
            ),
            encoding="utf-8",
        )
        (data_dir / "settled_facts.json").write_text(
            json.dumps(
                {
                    "schema": "memory-kit/v1",
                    "memory_type": "settled_facts",
                    "facts": [],
                    "anti_patterns": [],
                }
            ),
            encoding="utf-8",
        )
        (data_dir / "public_comms.json").write_text(
            json.dumps(
                {
                    "schema": "memory-kit/v1",
                    "memory_type": "public_comms",
                    "entries": [
                        {
                            "id": "PC-1",
                            "announcement_state": "do_not_repeat",
                            "topic": "metadata heading normalization commit e699943",
                            "message_summary": "Already announced",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (data_dir / "open_loops.json").write_text(
            json.dumps(
                {
                    "schema": "memory-kit/v1",
                    "memory_type": "open_loops",
                    "loops": [],
                    "parking_lot": [],
                }
            ),
            encoding="utf-8",
        )

    def _candidate_with_required_cues(self) -> str:
        return "\n".join(
            [
                "Day 419",
                "Goal: Improve your memory",
                "Room: #rest",
                "Email: gpt-5.4@agentvillage.org",
                "Memory Kit Path: /home/computeruse/gpt54-memory-kit",
                "metadata heading normalization commit e699943",
            ]
        )

    def test_normal_output_contains_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_store(data_dir)
            candidate = data_dir / "candidate.txt"
            candidate.write_text(self._candidate_with_required_cues(), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = main([str(data_dir), "--candidate", str(candidate), "--baseline-chars", "1000"])
            out = stdout.getvalue()

            self.assertEqual(0, rc)
            self.assertIn("CONSTRAINT TEST REPORT", out)
            self.assertIn(f"- Candidate path: {candidate.resolve()}", out)
            self.assertIn("- Baseline chars: 1000", out)
            self.assertIn("- Candidate total chars: ", out)
            self.assertIn("- Candidate embedded CHAR_COUNT: unknown", out)
            self.assertIn("- Candidate UTF-8 bytes: ", out)
            self.assertIn("- Reduction basis chars: ", out)
            self.assertIn("- Character reduction count: ", out)
            self.assertIn("- Reduction percent: ", out)
            self.assertIn("- Required anchor cue status: OK", out)
            self.assertIn("```markdown", out)
            self.assertIn("- PASS/FAIL + system text: PASS | System: Required anchors preserved.", out)

    def test_reduction_calculation_and_formatting(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_store(data_dir)
            candidate = data_dir / "candidate.txt"
            candidate.write_text("x" * 25, encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = main([str(data_dir), "--candidate", str(candidate), "--baseline-chars", "40"])
            out = stdout.getvalue()

            self.assertEqual(0, rc)
            self.assertIn("- Candidate total chars: 25", out)
            self.assertIn("- Character reduction count: 15", out)
            self.assertIn("- Reduction percent: 37.5%", out)

    def test_embedded_char_count_reported_when_present_or_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_store(data_dir)
            candidate_with_count = data_dir / "candidate-with-count.txt"
            body = self._candidate_with_required_cues() + "\n"
            candidate_with_count.write_text(f"{body}CHAR_COUNT={len(body)}\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = main([str(data_dir), "--candidate", str(candidate_with_count), "--baseline-chars", str(len(body))])
            out = stdout.getvalue()

            self.assertEqual(0, rc)
            self.assertIn(f"- Candidate embedded CHAR_COUNT: {len(body)}", out)
            self.assertIn(f"- Reduction basis chars: {len(body)}", out)
            self.assertIn("- Reduction percent: 0.0%", out)

    def test_result_text_is_included_when_supplied(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_store(data_dir)
            candidate = data_dir / "candidate.txt"
            candidate.write_text(self._candidate_with_required_cues(), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = main(
                    [
                        str(data_dir),
                        "--candidate",
                        str(candidate),
                        "--baseline-chars",
                        "1000",
                        "--agent",
                        "gpt-5.4",
                        "--target-label",
                        ">=30% reduction",
                        "--result-text",
                        "Ready to post in open loop.",
                    ]
                )
            out = stdout.getvalue()

            self.assertEqual(0, rc)
            self.assertIn("- agent: gpt-5.4", out)
            self.assertIn("- target reduction label: >=30% reduction", out)
            self.assertIn("- result text: Ready to post in open loop.", out)

    def test_unreadable_candidate_returns_nonzero_and_prints_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_store(data_dir)
            missing = data_dir / "missing.txt"

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = main([str(data_dir), "--candidate", str(missing), "--baseline-chars", "1000"])
            out = stdout.getvalue()

            self.assertEqual(1, rc)
            self.assertIn("ERROR: unable to read candidate file:", out)

    def test_baseline_chars_must_be_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_store(data_dir)
            candidate = data_dir / "candidate.txt"
            candidate.write_text(self._candidate_with_required_cues(), encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as ctx:
                    main([str(data_dir), "--candidate", str(candidate), "--baseline-chars", "0"])
            self.assertEqual(2, ctx.exception.code)


if __name__ == "__main__":
    unittest.main()
