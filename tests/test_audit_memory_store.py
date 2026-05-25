import json
import tempfile
import unittest
from pathlib import Path

from tools.audit_memory_store import audit_store, main


class AuditMemoryStoreTests(unittest.TestCase):
    def _write_valid_store(self, data_dir: Path) -> None:
        (data_dir / "identity_constraints.json").write_text(
            json.dumps(
                {
                    "schema": "memory-kit/v1",
                    "memory_type": "identity_constraints",
                    "principles": ["p1"],
                    "hard_rules": ["r1"],
                    "anchors": {"room": "#rest", "contact_email": "a@example.com"},
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
                    "focus": {"goal": "Improve your memory", "context": "day-419"},
                    "tasks": [
                        {
                            "id": "AF-1",
                            "summary": "task",
                            "status": "in_progress",
                            "priority": "high",
                            "next_action": "do it",
                        }
                    ],
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
                    "facts": [{"id": "SF-1", "statement": "Commit-hash anchoring works"}],
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
                            "topic": "status",
                            "announcement_state": "announced",
                            "message_summary": "sent",
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
                    "loops": [{"id": "OL-1", "question": "q", "priority": "high", "next_check": "n"}],
                    "parking_lot": [],
                }
            ),
            encoding="utf-8",
        )

    def test_schema_error_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            (data_dir / "open_loops.json").write_text(
                json.dumps({"schema": "memory-kit/v1", "memory_type": "open_loops", "parking_lot": []}),
                encoding="utf-8",
            )

            errors, warnings = audit_store(data_dir)
            self.assertTrue(errors)
            self.assertEqual([], warnings)
            self.assertNotEqual(0, main([str(data_dir)]))

    def test_warnings_only_still_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            (data_dir / "public_comms.json").write_text(
                json.dumps(
                    {
                        "schema": "memory-kit/v1",
                        "memory_type": "public_comms",
                        "entries": [
                            {
                                "id": "PC-1",
                                "topic": "status",
                                "announcement_state": "unknown_state",
                                "message_summary": "sent",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            errors, warnings = audit_store(data_dir)
            self.assertEqual([], errors)
            self.assertTrue(warnings)
            self.assertEqual(0, main([str(data_dir)]))


if __name__ == "__main__":
    unittest.main()
