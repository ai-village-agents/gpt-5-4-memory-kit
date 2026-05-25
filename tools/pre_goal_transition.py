#!/usr/bin/env python3
"""Run a practical pre-goal-transition check for the memory kit."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from audit_memory_store import audit_store
    from render_lean_memory import PRIORITY_RANK
    from validate_inventory import load_inventory, validate_inventory
else:
    from .audit_memory_store import audit_store
    from .render_lean_memory import PRIORITY_RANK
    from .validate_inventory import load_inventory, validate_inventory


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run pre-goal-transition checks")
    parser.add_argument("data_dir", nargs="?", default=None)
    parser.add_argument("--new-day", required=True, type=int)
    parser.add_argument("--new-goal", required=True)
    parser.add_argument("--source-summary", required=True)
    parser.add_argument("--new-room", default=None)
    return parser


def _run_git_cmd(args: List[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(args, check=False, capture_output=True, text=True)
    except OSError:
        return None


def _git_state() -> Tuple[str, str, bool]:
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


def _extract_day_from_context(context: str) -> int | None:
    match = re.search(r"\bday-(\d+)\b", context)
    if not match:
        return None
    return int(match.group(1))


def _current_day_goal_room(data_dir: Path) -> Tuple[int | None, str, str]:
    current_day: int | None = None
    current_goal = "unknown"
    current_room = "unknown"

    try:
        active_frontier = _load_json(data_dir / "active_frontier.json")
        focus = active_frontier.get("focus", {})
        current_goal_raw = str(focus.get("goal", "")).strip()
        if current_goal_raw:
            current_goal = current_goal_raw
        current_day = _extract_day_from_context(str(focus.get("context", "")))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        pass

    try:
        identity_constraints = _load_json(data_dir / "identity_constraints.json")
        anchors = identity_constraints.get("anchors", {})
        room_raw = str(anchors.get("room", "")).strip()
        if room_raw:
            current_room = room_raw
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        pass

    return current_day, current_goal, current_room


def _do_not_repeat_lines(data_dir: Path) -> List[str]:
    try:
        public_comms = _load_json(data_dir / "public_comms.json")
    except (FileNotFoundError, OSError, json.JSONDecodeError):
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
    except (FileNotFoundError, OSError, json.JSONDecodeError):
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


def _is_blank(value: str) -> bool:
    return not value.strip()


def _inventory_status(candidate_roots: List[Path]) -> Tuple[str, bool, bool]:
    inventory_path = None
    repo_root = None
    for root in candidate_roots:
        path = root / "inventory.yaml"
        if path.exists():
            inventory_path = path
            repo_root = root
            break

    if inventory_path is None or repo_root is None:
        return "unreadable", True, False

    try:
        data = load_inventory(inventory_path)
    except Exception:
        return "unreadable", True, False

    errors = validate_inventory(data, repo_root)
    if errors:
        return "invalid", False, True
    return "OK", False, False


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv or sys.argv[1:])

    if args.data_dir:
        data_dir = Path(args.data_dir).resolve()
    else:
        data_dir = Path(__file__).resolve().parents[1] / "data"

    current_day, current_goal, current_room = _current_day_goal_room(data_dir)
    dnr_lines = _do_not_repeat_lines(data_dir)
    loop_lines = _top_open_loop_lines(data_dir)
    repo_head, repo_status, repo_dirty = _git_state()
    errors, warnings = audit_store(data_dir)
    if errors:
        audit_status = "errors"
    elif warnings:
        audit_status = "warnings"
    else:
        audit_status = "OK"
    inventory_status, inventory_unreadable, inventory_invalid = _inventory_status([data_dir.parent, data_dir])

    proposed_room = args.new_room if args.new_room is not None else "(unchanged)"

    print("PRE-GOAL-TRANSITION CHECK")
    print(f"Current day: {current_day if current_day is not None else 'unknown'}")
    print(f"Current goal: {current_goal}")
    print(f"Current room: {current_room}")
    print(f"Proposed new day: {args.new_day}")
    print(f"Proposed new goal: {args.new_goal}")
    print(f"Proposed new room: {proposed_room}")
    print(f"Source summary: {args.source_summary}")
    print(f"Repo head: {repo_head}")
    print(f"Repo status: {repo_status}")
    print(f"Audit status: {audit_status}")
    print(f"Inventory status: {inventory_status}")
    print("Current do_not_repeat public-comms entries:")
    if dnr_lines:
        for line in dnr_lines:
            print(line)
    else:
        print("- none")
    print("Top open loops:")
    if loop_lines:
        for line in loop_lines:
            print(line)
    else:
        print("- none")

    reasons: List[str] = []
    if _is_blank(args.new_goal):
        reasons.append("--new-goal must not be blank")
    if _is_blank(args.source_summary):
        reasons.append("--source-summary must not be blank")
    if args.new_room is not None and _is_blank(args.new_room):
        reasons.append("--new-room must not be blank when provided")
    if audit_status == "errors":
        reasons.append("memory-store audit has errors")
    if repo_dirty:
        reasons.append("repo has uncommitted changes")
    if inventory_unreadable:
        reasons.append("inventory is unreadable")
    if inventory_invalid:
        reasons.append("inventory is invalid")
    if current_day is not None and args.new_day < current_day:
        reasons.append("--new-day must not be lower than current parsed day")

    if reasons:
        print(f"BLOCKED: {'; '.join(reasons)}")
        return 1

    print(
        "READY: apply the transition from visible-event text, then re-check public_comms and visible events before any announcement."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
