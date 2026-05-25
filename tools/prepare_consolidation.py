#!/usr/bin/env python3
"""Render lean memory to a candidate file, then run pre-consolidation checks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pre_consolidate
    from render_lean_memory import char_count_summary, render_lean_memory
else:
    from . import pre_consolidate
    from .render_lean_memory import char_count_summary, render_lean_memory


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render candidate and run pre-consolidation checks in one command.",
    )
    parser.add_argument("data_dir", nargs="?", default=None)
    parser.add_argument("--next-session-goal", required=True)
    parser.add_argument("--next-short-goal", required=True)
    parser.add_argument(
        "--candidate-path",
        default="/tmp/gpt54-memory-candidate.txt",
        help="Path to write the rendered candidate file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv or sys.argv[1:])

    if args.data_dir:
        data_dir = Path(args.data_dir).resolve()
    else:
        data_dir = Path(__file__).resolve().parents[1] / "data"

    candidate_path = Path(args.candidate_path).resolve()

    try:
        rendered = render_lean_memory(data_dir)
        candidate_path.write_text(rendered, encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: unable to write candidate file: {exc}")
        return 1

    candidate_total_chars, candidate_embedded_chars = char_count_summary(rendered)
    embedded_label = candidate_embedded_chars if candidate_embedded_chars is not None else "unknown"

    print("PREPARE-CONSOLIDATION")
    print(f"Candidate path: {candidate_path}")
    print(f"Candidate total chars: {candidate_total_chars}")
    print(f"Candidate embedded CHAR_COUNT: {embedded_label}")

    return pre_consolidate.main(
        [
            str(data_dir),
            "--next-session-goal",
            args.next_session_goal,
            "--next-short-goal",
            args.next_short_goal,
            "--candidate",
            str(candidate_path),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
