import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.render_lean_memory import main, render_lean_memory


class RenderLeanMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmpdir.name)

        (self.data_dir / "identity_constraints.json").write_text(
            '{"schema":"memory-kit/v1","memory_type":"identity_constraints","last_updated":"2026-05-25","principles":[],"hard_rules":["Follow the one-tool-call rule where that operational constraint applies.","Do not expose sensitive personal data in shared channels.","Do not re-announce already announced status updates without new substance."],"anchors":{"room":"#rest","contact_email":"gpt-5.4@agentvillage.org","memory_kit_path":"/home/computeruse/gpt54-memory-kit"},"do_not_store":[],"identity":{"room":"#rest","email":"gpt-5.4@agentvillage.org"}}',
            encoding="utf-8",
        )
        (self.data_dir / "active_frontier.json").write_text(
            '{"schema":"memory-kit/v1","memory_type":"active_frontier","last_updated":"2026-05-25","focus":{"context":"day-419 memory-improvement cycle","goal":"Improve your memory"},"tasks":[{"id":"AF-1","summary":"Task one","status":"in_progress","priority":"high","next_action":"Do one"},{"id":"AF-2","summary":"Task two","status":"in_progress","priority":"medium","next_action":"Do two"},{"id":"AF-3","summary":"Task three","status":"todo","priority":"high","next_action":"Do three"},{"id":"AF-4","summary":"Task four","status":"todo","priority":"low","next_action":"Do four"}],"high_priority_do_not_repeat":[]}',
            encoding="utf-8",
        )
        (self.data_dir / "settled_facts.json").write_text(
            '{"schema":"memory-kit/v1","memory_type":"settled_facts","last_updated":"2026-05-25","facts":[{"id":"SF-1","statement":"Fact one","stability":"high"},{"id":"SF-2","statement":"Fact two","stability":"medium"},{"id":"SF-3","statement":"Fact three","stability":"high"},{"id":"SF-4","statement":"Fact four","stability":"low"}],"anti_patterns":[]}',
            encoding="utf-8",
        )
        (self.data_dir / "public_comms.json").write_text(
            '{"schema":"memory-kit/v1","memory_type":"public_comms","last_updated":"2026-05-25","entries":[{"id":"PC-1","announcement_state":"do_not_repeat","topic":"topic a","message_summary":"summary a","date_day":416},{"id":"PC-2","announcement_state":"do_not_repeat","topic":"topic b","message_summary":"summary b","date_day":417},{"id":"PC-3","announcement_state":"announced","topic":"topic c","message_summary":"summary c","date_day":418},{"id":"PC-4","announcement_state":"announced","topic":"topic d","message_summary":"summary d","date_day":419},{"id":"PC-5","announcement_state":"announced","topic":"topic e","message_summary":"summary e","date_day":419}]}',
            encoding="utf-8",
        )
        (self.data_dir / "open_loops.json").write_text(
            '{"schema":"memory-kit/v1","memory_type":"open_loops","last_updated":"2026-05-25","loops":[{"id":"OL-1","priority":"medium","question":"Question one?","next_check":"Check one","status":"active"},{"id":"OL-2","priority":"high","question":"Question two?","next_check":"Check two","status":"active"},{"id":"OL-3","priority":"low","question":"Question three?","next_check":"Check three","status":"active"},{"id":"OL-4","priority":"low","question":"Question four?","next_check":"Check four","status":"active"}],"parking_lot":[]}',
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_render_includes_required_sections_in_order(self):
        rendered = render_lean_memory(self.data_dir)

        order = [
            "Day / goal anchor",
            "Identity / environment",
            "Hard rules",
            "Active frontier",
            "Settled facts",
            "Public comms cautions",
            "Open loops",
        ]

        start = -1
        for marker in order:
            idx = rendered.find(marker)
            self.assertGreater(idx, start)
            start = idx

    def test_render_contains_anchors_and_char_count(self):
        rendered = render_lean_memory(self.data_dir)

        self.assertIn("Room: #rest", rendered)
        self.assertIn("Email: gpt-5.4@agentvillage.org", rendered)
        self.assertIn("Memory Kit Path: /home/computeruse/gpt54-memory-kit", rendered)
        self.assertIn("Day 419", rendered)
        self.assertIn("CHAR_COUNT=", rendered)

    def test_render_limits_sections_to_requested_counts(self):
        rendered = render_lean_memory(self.data_dir)

        self.assertIn("Task one", rendered)
        self.assertIn("Task two", rendered)
        self.assertIn("Task three", rendered)
        self.assertNotIn("Task four", rendered)

        self.assertIn("Fact one", rendered)
        self.assertIn("Fact two", rendered)
        self.assertIn("Fact three", rendered)
        self.assertNotIn("Fact four", rendered)

        self.assertIn("Question one?", rendered)
        self.assertIn("Question two?", rendered)
        self.assertIn("Question three?", rendered)
        self.assertNotIn("Question four?", rendered)

    def test_render_keeps_all_do_not_repeat_but_only_recent_announced(self):
        rendered = render_lean_memory(self.data_dir)

        self.assertIn("topic a: summary a", rendered)
        self.assertIn("topic b: summary b", rendered)
        self.assertIn("topic d: summary d", rendered)
        self.assertIn("topic e: summary e", rendered)
        self.assertNotIn("topic c: summary c", rendered)

    def test_cli_default_prints_rendered_text(self):
        expected = render_lean_memory(self.data_dir)

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main([str(self.data_dir)])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), expected)

    def test_cli_write_writes_exact_text_and_prints_confirmation(self):
        destination = self.data_dir / "lean-memory.txt"
        expected = render_lean_memory(self.data_dir)

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main([str(self.data_dir), "--write", str(destination)])

        self.assertEqual(exit_code, 0)
        self.assertEqual(destination.read_text(encoding="utf-8"), expected)
        self.assertEqual(
            stdout.getvalue(),
            f"WROTE {destination} CHAR_COUNT={len(expected)}\n",
        )


if __name__ == "__main__":
    unittest.main()
