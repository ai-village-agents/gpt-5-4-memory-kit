import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools import validate_inventory


class ValidateInventoryTests(unittest.TestCase):
    def _write_inventory(self, root: Path, body: str) -> Path:
        path = root / "inventory.yaml"
        path.write_text(body, encoding="utf-8")
        return path

    def test_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "one.md").write_text("ok", encoding="utf-8")
            inv = self._write_inventory(
                root,
                (
                    "- id: item-1\n"
                    "  status: active\n"
                    "  kind: semantic\n"
                    "  summary: first\n"
                    "  source: docs/one.md\n"
                    "  last_verified: 2026-05-25\n"
                    "  retrieval_cue: cue\n"
                ),
            )
            buf = io.StringIO()
            with patch.object(validate_inventory, "REPO_ROOT", root):
                with redirect_stdout(buf):
                    rc = validate_inventory.main([str(inv)])
            output = buf.getvalue()
            self.assertEqual(0, rc)
            self.assertIn("INVENTORY CHECK", output)
            self.assertIn("Items: 1", output)
            self.assertIn("STATUS: OK", output)

    def test_missing_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inv = self._write_inventory(
                root,
                (
                    "- id: item-1\n"
                    "  status: active\n"
                    "  kind: semantic\n"
                    "  summary: first\n"
                    "  source: docs/one.md\n"
                    "  last_verified: 2026-05-25\n"
                    "  retrieval_cue: \n"
                ),
            )
            buf = io.StringIO()
            with patch.object(validate_inventory, "REPO_ROOT", root):
                with redirect_stdout(buf):
                    rc = validate_inventory.main([str(inv)])
            output = buf.getvalue()
            self.assertNotEqual(0, rc)
            self.assertIn("- item 1 missing non-blank field: retrieval_cue", output)
            self.assertIn("STATUS: ERROR", output)

    def test_duplicate_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inv = self._write_inventory(
                root,
                (
                    "- id: item-1\n"
                    "  status: active\n"
                    "  kind: semantic\n"
                    "  summary: first\n"
                    "  source: docs/one.md\n"
                    "  last_verified: 2026-05-25\n"
                    "  retrieval_cue: cue\n"
                    "- id: item-1\n"
                    "  status: active\n"
                    "  kind: semantic\n"
                    "  summary: second\n"
                    "  source: docs/two.md\n"
                    "  last_verified: 2026-05-25\n"
                    "  retrieval_cue: cue\n"
                ),
            )
            buf = io.StringIO()
            with patch.object(validate_inventory, "REPO_ROOT", root):
                with redirect_stdout(buf):
                    rc = validate_inventory.main([str(inv)])
            output = buf.getvalue()
            self.assertNotEqual(0, rc)
            self.assertIn("- duplicate id: item-1", output)
            self.assertIn("STATUS: ERROR", output)

    def test_nonexistent_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inv = self._write_inventory(
                root,
                (
                    "- id: item-1\n"
                    "  status: active\n"
                    "  kind: semantic\n"
                    "  summary: first\n"
                    "  source: docs/missing.md\n"
                    "  last_verified: 2026-05-25\n"
                    "  retrieval_cue: cue\n"
                ),
            )
            buf = io.StringIO()
            with patch.object(validate_inventory, "REPO_ROOT", root):
                with redirect_stdout(buf):
                    rc = validate_inventory.main([str(inv)])
            output = buf.getvalue()
            self.assertNotEqual(0, rc)
            self.assertIn("- source file not found: docs/missing.md", output)
            self.assertIn("STATUS: ERROR", output)


if __name__ == "__main__":
    unittest.main()
