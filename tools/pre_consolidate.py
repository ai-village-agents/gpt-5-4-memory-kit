#!/usr/bin/env python3
"""Run a practical pre-consolidation check for the memory kit."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from audit_memory_store import audit_store
    from check_memory_candidate import evaluate_memory_candidate
    from render_lean_memory import PRIORITY_RANK, render_lean_memory
else:
    from .audit_memory_store import audit_store
    from .check_memory_candidate import evaluate_memory_candidate
    from .render_lean_memory import PRIORITY_RANK, render_lean_memory


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run pre-consolidation checks")
    parser.add_argument("data_dir", nargs="?", default=None)
    parser.add_argument("--next-session-goal", required=True)
    parser.add_argument("--next-short-goal", required=True)
    parser.add_argument("--candidate", default=None, help="Path to consolidation candidate text file.")
    return parser


def _run_git_cmd(args: List[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(args, check=False, capture_output=True, text=True)
    except OSError:
        return None


def _git_state() -> tuple[str, str, bool]:
    head_cmd = _run_git_cmd(["git", "rev-parse", "--short", "HEAD"])
    status_cmd = _run_git_cmd(["git", "status", "--porcelain"])
    if (
        head_cmd is None
        or status_cmd is None
        or head_cmd.returncode != 0
        or status_cmd.returncode != 0
    ):
        return "unknown", "unknown", False

    head = head_cmd.stdout.strip() or "unknown"
    status_output = status_cmd.stdout.strip()
    status = "dirty" if status_output else "clean"
    return head, status, bool(status_output)


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _do_not_repeat_lines(data_dir: Path) -> List[str]:
    try:
        public_comms = _load_json(data_dir / "public_comms.json")
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    lines: List[str] = []
    for entry in public_comms.get("entries", []):
        state = str(entry.get("announcement_state", "")).strip().lower()
        if state != "do_not_repeat":
            continue
        entry_id = str(entry.get("id", "<unknown>"))
        topic = str(entry.get("topic", "")).strip() or "<no topic>"
        lines.append(f"- {entry_id}: {topic}")
    return lines


def _top_open_loop_lines(data_dir: Path) -> List[str]:
    try:
        open_loops = _load_json(data_dir / "open_loops.json")
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    loops = list(open_loops.get("loops", []))
    sorted_loops = sorted(
        loops,
        key=lambda item: (
            PRIORITY_RANK.get(str(item.get("priority", "")).strip().lower(), 99),
            str(item.get("id", "")),
        ),
    )

    lines: List[str] = []
    for loop in sorted_loops[:3]:
        loop_id = str(loop.get("id", "<unknown>"))
        question = str(loop.get("question", "")).strip() or "<no question>"
        lines.append(f"- {loop_id}: {question}")
    return lines


def _parse_char_count(rendered: str) -> str:
    match = re.search(r"CHAR_COUNT=(\d+)", rendered)
    if not match:
        return "unknown"
    return match.group(1)


def _is_blank(value: str) -> bool:
    return not value.strip()


def _word_count(value: str) -> int:
    return len(value.strip().split())


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv or sys.argv[1:])

    if args.data_dir:
        data_dir = Path(args.data_dir).resolve()
    else:
        data_dir = Path(__file__).resolve().parents[1] / "data"

    errors, warnings = audit_store(data_dir)
    if errors:
        audit_status = "errors"
    elif warnings:
        audit_status = "warnings"
    else:
        audit_status = "OK"

    try:
        rendered = render_lean_memory(data_dir)
        char_count = _parse_char_count(rendered)
    except Exception:
        char_count = "unknown"

    dnr_lines = _do_not_repeat_lines(data_dir)
    loop_lines = _top_open_loop_lines(data_dir)
    repo_head, repo_status, repo_dirty = _git_state()
    candidate_eval = None
    if args.candidate:
        candidate_eval = evaluate_memory_candidate(data_dir, Path(args.candidate).resolve())

    print("PRE-CONSOLIDATE CHECK")
    print(f"Next session goal: {args.next_session_goal}")
    print(f"Next short goal: {args.next_short_goal}")
    print(f"Repo head: {repo_head}")
    print(f"Repo status: {repo_status}")
    print(f"Audit status: {audit_status}")
    print(f"Rendered CHAR_COUNT: {char_count}")
    if candidate_eval is not None:
        print("Candidate check:")
        print(f"- Path: {candidate_eval.candidate_path}")
        if candidate_eval.read_error:
            print("- Candidate total chars: unknown")
            print("- Candidate embedded CHAR_COUNT: unknown")
            print("- Candidate cue status: BLOCKED")
        else:
            print(f"- Candidate total chars: {candidate_eval.candidate_total_chars}")
            embedded_chars = (
                candidate_eval.candidate_embedded_chars
                if candidate_eval.candidate_embedded_chars is not None
                else "unknown"
            )
            print(f"- Candidate embedded CHAR_COUNT: {embedded_chars}")
            print(f"- Candidate cue status: {'OK' if candidate_eval.all_found else 'WARN'}")
    print("Current do_not_repeat public-comms entries:")
    if dnr_lines:
        for line in dnr_lines:
            print(line)
    else:
        print("- none")
    print("Active open loops:")
    if loop_lines:
        for line in loop_lines:
            print(line)
    else:
        print("- none")

    reasons: List[str] = []
    if _is_blank(args.next_session_goal):
        reasons.append("--next-session-goal must not be blank")
    if _is_blank(args.next_short_goal):
        reasons.append("--next-short-goal must not be blank")
    if _word_count(args.next_short_goal) > 10:
        reasons.append("--next-short-goal must be 10 words or fewer")
    if len(args.next_short_goal.strip()) > 60:
        reasons.append("--next-short-goal must be 60 chars or fewer")
    if audit_status == "errors":
        reasons.append("memory-store audit has errors")
    if repo_dirty:
        reasons.append("repo has uncommitted changes")
    if candidate_eval is not None and candidate_eval.read_error:
        reasons.append("candidate file is unreadable")
    if candidate_eval is not None and not candidate_eval.read_error and not candidate_eval.all_found:
        reasons.append("candidate missing required cues or do_not_repeat topics")

    if reasons:
        print(f"BLOCKED: {'; '.join(reasons)}")
        return 1

    print("READY: review rendered lean memory and visible events before consolidating.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
