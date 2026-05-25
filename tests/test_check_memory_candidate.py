import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.check_memory_candidate import main


class CheckMemoryCandidateTests(unittest.TestCase):
    def _write_store(self, data_dir: Path) -> None:
        (data_dir / "identity_constraints.json").write_text(
            json.dumps(
                {
                    "schema": "memory-kit/v1",
                    "memory_type": "identity_constraints",
                    "principles": [],
                    "hard_rules": ["Rule one", "Rule two", "Rule three"],
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
                        },
                        {
                            "id": "PC-2",
                            "announcement_state": "do_not_repeat",
                            "topic": "possible future mention of commit 6813825",
                            "message_summary": "Hold unless checked",
                        },
                        {
                            "id": "PC-3",
                            "announcement_state": "announced",
                            "topic": "other",
                            "message_summary": "other",
                        },
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

    def test_ok_when_required_cues_and_topics_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_store(data_dir)
            candidate = data_dir / "candidate.txt"
            candidate.write_text(
                "\n".join(
                    [
                        "day 419",
                        "goal: improve your memory",
                        "room: #rest",
                        "email: gpt-5.4@agentvillage.org",
                        "memory kit path: /home/computeruse/gpt54-memory-kit",
                        "metadata heading normalization commit e699943",
                        "possible future mention of commit 6813825",
                    ]
                ),
                encoding="utf-8",
            )

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main([str(data_dir), "--candidate", str(candidate)])
            out = buf.getvalue()

            self.assertEqual(0, rc)
            self.assertIn("MEMORY CANDIDATE CHECK", out)
            self.assertIn("- Candidate embedded CHAR_COUNT: unknown", out)
            self.assertIn("- Rendered embedded CHAR_COUNT: ", out)
            self.assertIn("FOUND | inferred day line | Day 419", out)
            self.assertIn("FOUND | goal string | Goal: Improve your memory", out)
            self.assertIn("FOUND | metadata heading normalization commit e699943", out)
            self.assertIn("FOUND | possible future mention of commit 6813825", out)
            self.assertIn("- STATUS: OK", out)

    def test_warn_when_required_anchor_cue_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_store(data_dir)
            candidate = data_dir / "candidate.txt"
            candidate.write_text(
                "\n".join(
                    [
                        "day 419",
                        "goal: improve your memory",
                        "room: #rest",
                        "metadata heading normalization commit e699943",
                        "possible future mention of commit 6813825",
                    ]
                ),
                encoding="utf-8",
            )

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main([str(data_dir), "--candidate", str(candidate)])
            out = buf.getvalue()

            self.assertEqual(0, rc)
            self.assertIn("MISSING | email | Email: gpt-5.4@agentvillage.org", out)
            self.assertIn("- STATUS: WARN", out)

    def test_warn_when_do_not_repeat_topic_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_store(data_dir)
            candidate = data_dir / "candidate.txt"
            candidate.write_text(
                "\n".join(
                    [
                        "day 419",
                        "goal: improve your memory",
                        "room: #rest",
                        "email: gpt-5.4@agentvillage.org",
                        "memory kit path: /home/computeruse/gpt54-memory-kit",
                        "metadata heading normalization commit e699943",
                    ]
                ),
                encoding="utf-8",
            )

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main([str(data_dir), "--candidate", str(candidate)])
            out = buf.getvalue()

            self.assertEqual(0, rc)
            self.assertIn("MISSING | possible future mention of commit 6813825", out)
            self.assertIn("- STATUS: WARN", out)

    def test_reports_parseable_candidate_embedded_char_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_store(data_dir)
            candidate = data_dir / "candidate.txt"
            body = "\n".join(
                [
                    "day 419",
                    "goal: improve your memory",
                    "room: #rest",
                    "email: gpt-5.4@agentvillage.org",
                    "memory kit path: /home/computeruse/gpt54-memory-kit",
                    "metadata heading normalization commit e699943",
                    "possible future mention of commit 6813825",
                ]
            )
            candidate.write_text(
                f"{body}\nCHAR_COUNT={len(body) + 1}\n",
                encoding="utf-8",
            )

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main([str(data_dir), "--candidate", str(candidate)])
            out = buf.getvalue()

            self.assertEqual(0, rc)
            self.assertIn(f"- Candidate embedded CHAR_COUNT: {len(body) + 1}", out)
            self.assertIn("- STATUS: OK", out)


if __name__ == "__main__":
    unittest.main()
