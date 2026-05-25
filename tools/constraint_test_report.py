#!/usr/bin/env python3
"""Generate a standardized constraint-test report for memory candidates."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from check_memory_candidate import evaluate_memory_candidate
    from render_lean_memory import char_count_summary
except ModuleNotFoundError:
    from .check_memory_candidate import evaluate_memory_candidate
    from .render_lean_memory import char_count_summary

PASS_SYSTEM_TEXT = "System: Required anchors preserved."
FAIL_SYSTEM_TEXT = "System: Required anchors missing."


def _positive_int(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return value


def constraint_test_report(
    data_dir: Path,
    candidate_path: Path,
    baseline_chars: int,
    agent: str | None = None,
    result_text: str | None = None,
    target_label: str | None = None,
) -> int:
    evaluation = evaluate_memory_candidate(data_dir, candidate_path)
    if evaluation.read_error:
        print(f"ERROR: unable to read candidate file: {evaluation.read_error}")
        return 1

    candidate_text = candidate_path.read_text(encoding="utf-8")
    candidate_total_chars, candidate_embedded_chars = char_count_summary(candidate_text)
    candidate_utf8_bytes = len(candidate_text.encode("utf-8"))
    reduction_basis_chars = (
        candidate_embedded_chars if candidate_embedded_chars is not None else candidate_total_chars
    )
    reduction_count = baseline_chars - reduction_basis_chars
    reduction_percent = (reduction_count / baseline_chars) * 100.0
    anchor_status = "OK" if evaluation.all_found else "WARN"
    required_anchors_preserved = "yes" if evaluation.all_found else "no"
    pass_fail = "PASS" if evaluation.all_found else "FAIL"
    system_text = PASS_SYSTEM_TEXT if evaluation.all_found else FAIL_SYSTEM_TEXT
    embedded_label = (
        str(candidate_embedded_chars) if candidate_embedded_chars is not None else "unknown"
    )
    target_label_value = target_label if target_label else "unspecified"
    agent_value = agent if agent else "unspecified"

    print("CONSTRAINT TEST REPORT")
    print(f"- Candidate path: {candidate_path}")
    print(f"- Baseline chars: {baseline_chars}")
    print(f"- Candidate total chars: {candidate_total_chars}")
    print(f"- Candidate embedded CHAR_COUNT: {embedded_label}")
    print(f"- Candidate UTF-8 bytes: {candidate_utf8_bytes}")
    print(f"- Reduction basis chars: {reduction_basis_chars}")
    print(f"- Character reduction count: {reduction_count}")
    print(f"- Reduction percent: {reduction_percent:.1f}%")
    print(f"- Required anchor cue status: {anchor_status}")
    print("")
    print("```markdown")
    print(f"- agent: {agent_value}")
    print(f"- baseline internal-memory char count: {baseline_chars}")
    print(f"- candidate total chars: {candidate_total_chars}")
    print(f"- candidate embedded CHAR_COUNT: {embedded_label}")
    print(f"- candidate UTF-8 bytes: {candidate_utf8_bytes}")
    print(f"- target reduction label: {target_label_value}")
    print(f"- actual reduction percent: {reduction_percent:.1f}%")
    print(
        "- count method: Python len(text) chars and len(text.encode('utf-8')) UTF-8 bytes; reduction uses embedded CHAR_COUNT when present, else total chars"
    )
    print(f"- required anchors preserved: {required_anchors_preserved}")
    print(f"- PASS/FAIL + system text: {pass_fail} | {system_text}")
    if result_text:
        print(f"- result text: {result_text}")
    print(f"- candidate path: {candidate_path}")
    print("```")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a standard report for consolidation-threshold experiments.",
    )
    parser.add_argument(
        "data_dir",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1] / "data"),
        help="Path to the data directory (defaults to repo data/).",
    )
    parser.add_argument("--candidate", required=True, help="Path to candidate text file.")
    parser.add_argument(
        "--baseline-chars",
        required=True,
        type=_positive_int,
        help="Baseline internal-memory char count (must be > 0).",
    )
    parser.add_argument("--agent", help="Optional agent identifier for report template.")
    parser.add_argument("--result-text", help="Optional result summary to include in template.")
    parser.add_argument("--target-label", help="Optional target reduction label.")
    args = parser.parse_args(argv or sys.argv[1:])

    return constraint_test_report(
        data_dir=Path(args.data_dir).resolve(),
        candidate_path=Path(args.candidate).resolve(),
        baseline_chars=args.baseline_chars,
        agent=args.agent,
        result_text=args.result_text,
        target_label=args.target_label,
    )


if __name__ == "__main__":
    raise SystemExit(main())
