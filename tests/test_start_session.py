import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

try:
    from tests.test_audit_memory_store import AuditMemoryStoreTests
except ModuleNotFoundError:
    from test_audit_memory_store import AuditMemoryStoreTests
from tools.start_session import main


class StartSessionTests(unittest.TestCase):
    def test_start_session_inventory_ok_with_nearby_inventory(self):
        helper = AuditMemoryStoreTests()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            data_dir.mkdir()
            helper._write_valid_store(data_dir)
            (root / "docs").mkdir()
            (root / "docs" / "one.md").write_text("ok", encoding="utf-8")
            (root / "inventory.yaml").write_text(
                (
                    "- id: item-1\n"
                    "  status: active\n"
                    "  kind: semantic\n"
                    "  summary: first\n"
                    "  source: docs/one.md\n"
                    "  last_verified: 2026-05-25\n"
                    "  retrieval_cue: cue\n"
                ),
                encoding="utf-8",
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main([str(data_dir)])
            out = buf.getvalue()
            self.assertEqual(0, rc)
            self.assertIn('SESSION BRIEF', out)
            self.assertIn('SESSION START CHECK', out)
            self.assertIn('Audit status: OK', out)
            self.assertIn('Inventory status: OK', out)

    def test_start_session_inventory_skipped_when_missing(self):
        helper = AuditMemoryStoreTests()
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            helper._write_valid_store(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main([str(data_dir)])
            out = buf.getvalue()
            self.assertEqual(0, rc)
            self.assertIn('Audit status: OK', out)
            self.assertIn('Inventory status: skipped (inventory.yaml not found)', out)

    def test_start_session_inventory_error_is_nonblocking(self):
        helper = AuditMemoryStoreTests()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            data_dir.mkdir()
            helper._write_valid_store(data_dir)
            (root / "inventory.yaml").write_text(
                (
                    "- id: item-1\n"
                    "  status: active\n"
                    "  kind: semantic\n"
                    "  summary: first\n"
                    "  source: docs/missing.md\n"
                    "  last_verified: 2026-05-25\n"
                    "  retrieval_cue: cue\n"
                ),
                encoding="utf-8",
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main([str(data_dir)])
            out = buf.getvalue()
            self.assertEqual(0, rc)
            self.assertIn('Inventory status: warnings/errors present', out)
            self.assertIn('source file not found: docs/missing.md', out)


if __name__ == '__main__':
    unittest.main()
