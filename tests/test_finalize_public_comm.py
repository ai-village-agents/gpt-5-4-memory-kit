import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.finalize_public_comm import main
from tests.test_audit_memory_store import AuditMemoryStoreTests


class FinalizePublicCommTests(unittest.TestCase):
    def _write_valid_store(self, data_dir: Path) -> None:
        AuditMemoryStoreTests()._write_valid_store(data_dir)

    def test_success_logs_then_prunes(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            (data_dir / "public_comms.json").write_text(
                json.dumps(
                    {
                        "schema": "memory-kit/v1",
                        "memory_type": "public_comms",
                        "last_updated": "2026-05-25",
                        "entries": [
                            {
                                "id": "PC-1",
                                "announcement_state": "announced",
                                "topic": "old topic a",
                                "message_summary": "older send",
                                "audience": "#rest",
                                "date_day": 418,
                            },
                            {
                                "id": "PC-2",
                                "announcement_state": "announced",
                                "topic": "old topic b",
                                "message_summary": "newer send",
                                "audience": "#rest",
                                "date_day": 419,
                            },
                            {
                                "id": "PC-3",
                                "announcement_state": "do_not_repeat",
                                "topic": "safety note",
                                "message_summary": "never resend",
                                "audience": "#rest",
                                "date_day": 419,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--state",
                        "announced",
                        "--topic",
                        "fresh topic",
                        "--message-summary",
                        "posted fresh update",
                        "--audience",
                        "#rest",
                        "--date-day",
                        "420",
                    ]
                )
            out = buf.getvalue()

            self.assertEqual(0, rc)
            self.assertIn("FINALIZE-PUBLIC-COMM", out)
            self.assertIn("LOGGED:", out)
            self.assertIn("PRUNE-PUBLIC-COMMS", out)
            self.assertIn("FINALIZED:", out)

            active = json.loads((data_dir / "public_comms.json").read_text(encoding="utf-8"))
            topics = [entry.get("topic") for entry in active.get("entries", [])]
            self.assertIn("fresh topic", topics)
            active_announced = [
                entry
                for entry in active.get("entries", [])
                if str(entry.get("announcement_state", "")).strip().lower() == "announced"
            ]
            self.assertLessEqual(len(active_announced), 2)

    def test_duplicate_topic_blocks_and_skips_prune(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--state",
                        "announced",
                        "--topic",
                        "status",
                        "--message-summary",
                        "duplicate message",
                        "--audience",
                        "#rest",
                        "--date-day",
                        "420",
                    ]
                )
            out = buf.getvalue()

            self.assertNotEqual(0, rc)
            self.assertIn("BLOCKED: duplicate state+topic already exists", out)
            self.assertNotIn("PRUNE-PUBLIC-COMMS", out)

    def test_keep_announced_passthrough(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_valid_store(data_dir)
            (data_dir / "public_comms.json").write_text(
                json.dumps(
                    {
                        "schema": "memory-kit/v1",
                        "memory_type": "public_comms",
                        "last_updated": "2026-05-25",
                        "entries": [
                            {
                                "id": "PC-1",
                                "announcement_state": "announced",
                                "topic": "older",
                                "message_summary": "older send",
                                "audience": "#rest",
                                "date_day": 410,
                            },
                            {
                                "id": "PC-2",
                                "announcement_state": "announced",
                                "topic": "middle",
                                "message_summary": "middle send",
                                "audience": "#rest",
                                "date_day": 411,
                            },
                            {
                                "id": "PC-3",
                                "announcement_state": "announced",
                                "topic": "newest before wrapper",
                                "message_summary": "newest send",
                                "audience": "#rest",
                                "date_day": 412,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--state",
                        "announced",
                        "--topic",
                        "final newest",
                        "--message-summary",
                        "most recent send",
                        "--audience",
                        "#rest",
                        "--date-day",
                        "420",
                        "--keep-announced",
                        "1",
                    ]
                )
            self.assertEqual(0, rc)

            active = json.loads((data_dir / "public_comms.json").read_text(encoding="utf-8"))
            active_announced = [
                entry
                for entry in active.get("entries", [])
                if str(entry.get("announcement_state", "")).strip().lower() == "announced"
            ]
            self.assertEqual(1, len(active_announced))


if __name__ == "__main__":
    unittest.main()
