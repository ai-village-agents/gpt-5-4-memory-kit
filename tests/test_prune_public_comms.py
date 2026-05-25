import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.prune_public_comms import main


class PrunePublicCommsTests(unittest.TestCase):
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
                            "topic": "do not repeat one",
                            "message_summary": "keep this",
                            "audience": "#rest",
                            "date_day": 100,
                        },
                        {
                            "id": "PC-2",
                            "announcement_state": "announced",
                            "topic": "old announced",
                            "message_summary": "older",
                            "audience": "#rest",
                            "date_day": 410,
                        },
                        {
                            "id": "PC-3",
                            "announcement_state": "announced",
                            "topic": "newer announced",
                            "message_summary": "newer",
                            "audience": "#rest",
                            "date_day": 420,
                        },
                        {
                            "id": "PC-4",
                            "announcement_state": "announced",
                            "topic": "same day lower id",
                            "message_summary": "same day lower",
                            "audience": "#rest",
                            "date_day": 421,
                        },
                        {
                            "id": "PC-5",
                            "announcement_state": "announced",
                            "topic": "same day higher id",
                            "message_summary": "same day higher",
                            "audience": "#rest",
                            "date_day": 421,
                        },
                        {
                            "id": "PC-X",
                            "announcement_state": "pending",
                            "topic": "nonstandard state",
                            "message_summary": "leave untouched",
                            "audience": "#rest",
                            "date_day": 1,
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

    def test_prunes_older_announced_keeps_do_not_repeat_and_newest_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main([str(data_dir)])

            self.assertEqual(0, rc)
            out = buf.getvalue()
            self.assertIn("PRUNE-PUBLIC-COMMS", out)
            self.assertIn("KEPT_ANNOUNCED: 2", out)
            self.assertIn("ARCHIVED_THIS_RUN: 2", out)
            self.assertIn("STATUS: OK", out)

            active = json.loads((data_dir / "public_comms.json").read_text(encoding="utf-8"))
            active_ids = [entry["id"] for entry in active["entries"]]
            self.assertEqual(["PC-1", "PC-4", "PC-5", "PC-X"], active_ids)

            archive = json.loads(
                (data_dir / "public_comms_archive.json").read_text(encoding="utf-8")
            )
            self.assertEqual("memory-kit/v1", archive["schema"])
            self.assertEqual("public_comms_archive", archive["memory_type"])
            self.assertEqual("2026-05-25", archive["last_updated"])
            archived_ids = [entry["id"] for entry in archive["entries"]]
            self.assertEqual(["PC-2", "PC-3"], archived_ids)

            # Pretty-printed with trailing newline.
            self.assertTrue((data_dir / "public_comms.json").read_text(encoding="utf-8").endswith("\n"))
            self.assertTrue(
                (data_dir / "public_comms_archive.json").read_text(encoding="utf-8").endswith("\n")
            )

    def test_no_op_when_nothing_needs_archiving(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            (data_dir / "public_comms.json").write_text(
                json.dumps(
                    {
                        "schema": "memory-kit/v1",
                        "memory_type": "public_comms",
                        "last_updated": "2026-05-24",
                        "entries": [
                            {
                                "id": "PC-1",
                                "announcement_state": "do_not_repeat",
                                "topic": "only dnr",
                                "message_summary": "keep",
                                "audience": "#rest",
                                "date_day": 101,
                            },
                            {
                                "id": "PC-2",
                                "announcement_state": "announced",
                                "topic": "first",
                                "message_summary": "keep",
                                "audience": "#rest",
                                "date_day": 102,
                            },
                            {
                                "id": "PC-3",
                                "announcement_state": "announced",
                                "topic": "second",
                                "message_summary": "keep",
                                "audience": "#rest",
                                "date_day": 103,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main([str(data_dir)])

            self.assertEqual(0, rc)
            out = buf.getvalue()
            self.assertIn("ARCHIVED_THIS_RUN: 0", out)
            self.assertIn("STATUS: NO-OP", out)
            self.assertIn("ARCHIVE_TOTAL: 0", out)

            archive = json.loads(
                (data_dir / "public_comms_archive.json").read_text(encoding="utf-8")
            )
            self.assertEqual([], archive["entries"])

    def test_archive_dedup_skips_existing_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self._write_public_comms(data_dir)
            (data_dir / "public_comms_archive.json").write_text(
                json.dumps(
                    {
                        "schema": "memory-kit/v1",
                        "memory_type": "public_comms_archive",
                        "last_updated": "2026-05-20",
                        "entries": [
                            {
                                "id": "PC-2",
                                "announcement_state": "announced",
                                "topic": "old announced",
                                "message_summary": "already archived copy",
                                "audience": "#rest",
                                "date_day": 410,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main([str(data_dir)])

            self.assertEqual(0, rc)
            out = buf.getvalue()
            self.assertIn("ARCHIVED_THIS_RUN: 1", out)
            self.assertIn("ARCHIVE_TOTAL: 2", out)

            archive = json.loads(
                (data_dir / "public_comms_archive.json").read_text(encoding="utf-8")
            )
            archived_ids = [entry["id"] for entry in archive["entries"]]
            self.assertEqual(["PC-2", "PC-3"], archived_ids)


if __name__ == "__main__":
    unittest.main()
