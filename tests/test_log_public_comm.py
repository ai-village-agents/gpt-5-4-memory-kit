import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.log_public_comm import main


class LogPublicCommTests(unittest.TestCase):
    def _write_public_comms(self, data_dir: Path) -> None:
        (data_dir / "public_comms.json").write_text(
            json.dumps(
                {
                    "schema": "memory-kit/v1",
                    "memory_type": "public_comms",
                    "last_updated": "2026-05-25",
                    "entries": [
                        {
                            "id": "PC-1",
                            "announcement_state": "do_not_repeat",
                            "topic": "existing warning",
                            "message_summary": "already tracked",
                            "audience": "#rest",
                            "date_day": 410,
                        },
                        {
                            "id": "PC-4",
                            "announcement_state": "announced",
                            "topic": "already announced thing",
                            "message_summary": "already posted",
                            "audience": "#rest",
                            "date_day": 411,
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

    def test_success_append_and_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--state",
                        "announced",
                        "--topic",
                        "new rollout",
                        "--message-summary",
                        "posted public rollout update",
                        "--audience",
                        "#rest",
                        "--date-day",
                        "420",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(0, rc)
            self.assertIn("PUBLIC COMMS LOG", out)
            self.assertIn("LOGGED: PC-5", out)

            obj = json.loads((data_dir / "public_comms.json").read_text(encoding="utf-8"))
            self.assertEqual("memory-kit/v1", obj["schema"])
            new_entry = obj["entries"][-1]
            self.assertEqual(
                {
                    "id": "PC-5",
                    "announcement_state": "announced",
                    "topic": "new rollout",
                    "message_summary": "posted public rollout update",
                    "audience": "#rest",
                    "date_day": 420,
                },
                new_entry,
            )

    def test_blocked_blank_topic(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--state",
                        "announced",
                        "--topic",
                        "   ",
                        "--message-summary",
                        "posted public rollout update",
                        "--audience",
                        "#rest",
                        "--date-day",
                        "420",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("BLOCKED: --topic must not be blank", out)

    def test_blocked_invalid_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--state",
                        "posted",
                        "--topic",
                        "new rollout",
                        "--message-summary",
                        "posted public rollout update",
                        "--audience",
                        "#rest",
                        "--date-day",
                        "420",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("BLOCKED: --state must be announced or do_not_repeat", out)

    def test_blocked_duplicate_topic_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--state",
                        "announced",
                        "--topic",
                        "  ALREADY ANNOUNCED THING  ",
                        "--message-summary",
                        "posted public rollout update",
                        "--audience",
                        "#rest",
                        "--date-day",
                        "420",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("BLOCKED: duplicate state+topic already exists", out)


    def test_blocked_duplicate_topic_state_found_in_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            (data_dir / "public_comms_archive.json").write_text(
                json.dumps(
                    {
                        "schema": "memory-kit/v1",
                        "memory_type": "public_comms_archive",
                        "entries": [
                            {
                                "id": "PC-7",
                                "announcement_state": "announced",
                                "topic": "archived topic",
                                "message_summary": "older archived send",
                                "audience": "#rest",
                                "date_day": 409,
                            }
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
                        " ARCHIVED TOPIC ",
                        "--message-summary",
                        "posted public rollout update",
                        "--audience",
                        "#rest",
                        "--date-day",
                        "420",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("BLOCKED: duplicate state+topic already exists", out)

    def test_success_next_id_uses_archive_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            (data_dir / "public_comms_archive.json").write_text(
                json.dumps(
                    {
                        "schema": "memory-kit/v1",
                        "memory_type": "public_comms_archive",
                        "entries": [
                            {
                                "id": "PC-9",
                                "announcement_state": "announced",
                                "topic": "older archived send",
                                "message_summary": "already archived",
                                "audience": "#rest",
                                "date_day": 409,
                            }
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
                        "new rollout",
                        "--message-summary",
                        "posted public rollout update",
                        "--audience",
                        "#rest",
                        "--date-day",
                        "420",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(0, rc)
            self.assertIn("LOGGED: PC-10", out)

            obj = json.loads((data_dir / "public_comms.json").read_text(encoding="utf-8"))
            self.assertEqual("PC-10", obj["entries"][-1]["id"])

    def test_blocked_invalid_day_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--state",
                        "announced",
                        "--topic",
                        "new rollout",
                        "--message-summary",
                        "posted public rollout update",
                        "--audience",
                        "#rest",
                        "--date-day",
                        "0",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("BLOCKED: --date-day must be a positive integer", out)


if __name__ == "__main__":
    unittest.main()
