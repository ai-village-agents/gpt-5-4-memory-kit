import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from test_audit_memory_store import AuditMemoryStoreTests
from tools.start_session import main


class StartSessionTests(unittest.TestCase):
    def test_start_session_prints_check(self):
        helper = AuditMemoryStoreTests()
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            helper._write_valid_store(data_dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main([str(data_dir)])
            out = buf.getvalue()
            self.assertEqual(0, rc)
            self.assertIn('SESSION BRIEF', out)
            self.assertIn('SESSION START CHECK', out)
            self.assertIn('Audit status: OK', out)


if __name__ == '__main__':
    unittest.main()
