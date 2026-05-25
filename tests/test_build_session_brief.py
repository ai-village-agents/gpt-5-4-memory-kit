import tempfile
import unittest
from pathlib import Path

from tools.build_session_brief import build_brief


class BuildSessionBriefTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmpdir.name)

        (self.data_dir / "identity_constraints.json").write_text(
            '{"schema":"memory-kit/v1","memory_type":"identity_constraints","last_updated":"2026-05-25","principles":[],"hard_rules":["one-tool-call rule"],"anchors":{"room":"#rest","contact_email":"ops@example.com"},"do_not_store":[]}',
            encoding="utf-8",
        )
        (self.data_dir / "active_frontier.json").write_text(
            '{"schema":"memory-kit/v1","memory_type":"active_frontier","last_updated":"2026-05-25","focus":{"context":"day-419","goal":"Improve your memory"},"tasks":[{"id":"AF-1","summary":"Keep brief small","priority":"high","next_action":"Use brief"}],"high_priority_do_not_repeat":["Do not duplicate e699943 announcement"]}',
            encoding="utf-8",
        )
        (self.data_dir / "settled_facts.json").write_text(
            '{"schema":"memory-kit/v1","memory_type":"settled_facts","last_updated":"2026-05-25","facts":[{"id":"SF-1","statement":"Commit-hash anchoring helps"}],"anti_patterns":[]}',
            encoding="utf-8",
        )
        (self.data_dir / "public_comms.json").write_text(
            '{"schema":"memory-kit/v1","memory_type":"public_comms","last_updated":"2026-05-25","entries":['
            '{"id":"PC-1","topic":"do not repeat old thing","announcement_state":"do_not_repeat","message_summary":"already visible","date_day":416},'
            '{"id":"PC-2","topic":"older announced","announcement_state":"announced","message_summary":"old update","date_day":419},'
            '{"id":"PC-3","topic":"newer announced","announcement_state":"announced","message_summary":"new update","date_day":419},'
            '{"id":"PC-4","topic":"newest announced","announcement_state":"announced","message_summary":"newest update","date_day":420}'
            ']}',
            encoding="utf-8",
        )
        (self.data_dir / "open_loops.json").write_text(
            '{"schema":"memory-kit/v1","memory_type":"open_loops","last_updated":"2026-05-25","loops":[{"id":"OL-1","question":"What threshold?","priority":"high","next_check":"Discuss tomorrow"}],"parking_lot":[]}',
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_brief_contains_stable_order_and_key_sections(self):
        brief = build_brief(self.data_dir)

        order = [
            "1) identity_constraints",
            "2) active_frontier",
            "3) settled_facts",
            "4) public_comms",
            "5) open_loops",
        ]

        start = -1
        for marker in order:
            idx = brief.find(marker)
            self.assertGreater(idx, start)
            start = idx

        self.assertIn("HIGH PRIORITY DO-NOT-REPEAT", brief)
        self.assertIn("What threshold?", brief)
        self.assertIn("do not repeat old thing", brief)
        self.assertIn("newest announced", brief)
        self.assertIn("newer announced", brief)
        self.assertNotIn("older announced", brief)


if __name__ == "__main__":
    unittest.main()
