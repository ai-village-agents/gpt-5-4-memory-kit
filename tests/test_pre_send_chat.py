import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.pre_send_chat import main


class PreSendChatTests(unittest.TestCase):
    def _write_public_comms(self, data_dir: Path) -> None:
        (data_dir / "public_comms.json").write_text(
            json.dumps(
                {
                    "schema": "memory-kit/v1",
                    "memory_type": "public_comms",
                    "entries": [
                        {
                            "id": "PC-1",
                            "announcement_state": "do_not_repeat",
                            "topic": "already announced status update",
                        },
                        {
                            "id": "PC-2",
                            "announcement_state": "announced",
                            "topic": "other note",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

    def _write_public_comms_archive(self, data_dir: Path) -> None:
        (data_dir / "public_comms_archive.json").write_text(
            json.dumps(
                {
                    "schema": "memory-kit/v1",
                    "memory_type": "public_comms",
                    "entries": [
                        {
                            "id": "PC-ARCH-1",
                            "announcement_state": "announced",
                            "topic": "archived milestone note",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def test_success_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--purpose",
                        "share status",
                        "--recipient",
                        "#rest",
                        "--topic",
                        "checkpoint summary",
                        "--duplicate-check",
                        "Compared against visible AGENT_TALK events for this topic",
                        "--visible-events-check",
                        "Re-checked latest visible AGENT_TALK events before send",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(0, rc)
            self.assertIn("PRE-SEND CHAT CHECK", out)
            self.assertIn("- PC-1: already announced status update", out)
            self.assertIn(
                "- Visible-events-check: Re-checked latest visible AGENT_TALK events before send",
                out,
            )
            self.assertIn(
                "READY: public_comms passed; re-check the latest visible events immediately before sending.",
                out,
            )

    def test_blocked_blank_required_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--purpose",
                        "   ",
                        "--recipient",
                        "#rest",
                        "--topic",
                        "checkpoint summary",
                        "--duplicate-check",
                        "Compared with existing visible status updates",
                        "--visible-events-check",
                        "Re-checked latest visible status events before send",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("BLOCKED: --purpose must not be blank", out)

    def test_blocked_vague_duplicate_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--purpose",
                        "share status",
                        "--recipient",
                        "#rest",
                        "--topic",
                        "checkpoint summary",
                        "--duplicate-check",
                        "ok",
                        "--visible-events-check",
                        "Re-checked latest visible status events before send",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("BLOCKED: --duplicate-check is too vague", out)

    def test_blocked_blank_visible_events_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--purpose",
                        "share status",
                        "--recipient",
                        "#rest",
                        "--topic",
                        "checkpoint summary",
                        "--duplicate-check",
                        "Compared with existing visible status updates",
                        "--visible-events-check",
                        "   ",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("BLOCKED: --visible-events-check must not be blank", out)

    def test_blocked_vague_visible_events_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--purpose",
                        "share status",
                        "--recipient",
                        "#rest",
                        "--topic",
                        "checkpoint summary",
                        "--duplicate-check",
                        "Compared with existing visible status updates",
                        "--visible-events-check",
                        "checked",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn("BLOCKED: --visible-events-check is too vague", out)

    def test_blocked_duplicate_topic_in_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--purpose",
                        "share status",
                        "--recipient",
                        "#rest",
                        "--topic",
                        "  ALREADY ANNOUNCED STATUS UPDATE  ",
                        "--duplicate-check",
                        "Compared against existing entries and visible event log",
                        "--visible-events-check",
                        "Re-checked latest visible event log before sending",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn(
                "BLOCKED: --topic already exists in public_comms (id=PC-1, announcement_state=do_not_repeat)",
                out,
            )

    def test_blocked_duplicate_topic_in_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            self._write_public_comms_archive(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        str(data_dir),
                        "--purpose",
                        "share status",
                        "--recipient",
                        "#rest",
                        "--topic",
                        " ARCHIVED MILESTONE NOTE ",
                        "--duplicate-check",
                        "Compared against existing entries and visible event log",
                        "--visible-events-check",
                        "Re-checked latest visible event log before sending",
                    ]
                )
            out = buf.getvalue()
            self.assertEqual(1, rc)
            self.assertIn(
                "BLOCKED: --topic already exists in public_comms (id=PC-ARCH-1, announcement_state=announced)",
                out,
            )


if __name__ == "__main__":
    unittest.main()
