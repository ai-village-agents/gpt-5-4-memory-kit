#!/usr/bin/env python3
"""Check a real consolidation candidate against required lean-memory cues."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from render_lean_memory import _infer_day, render_lean_memory
except ModuleNotFoundError:
    from .render_lean_memory import _infer_day, render_lean_memory

FILES = [
    "identity_constraints",
    "active_frontier",
    "settled_facts",
    "public_comms",
    "open_loops",
]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_store(data_dir: Path) -> Dict[str, Dict[str, Any]]:
    store: Dict[str, Dict[str, Any]] = {}
    for name in FILES:
        store[name] = _load_json(data_dir / f"{name}.json")
    return store


def _required_anchor_cues(store: Dict[str, Dict[str, Any]]) -> List[Tuple[str, str]]:
    identity = store["identity_constraints"]
    frontier = store["active_frontier"]

    focus = frontier.get("focus", {})
    context = str(focus.get("context", "")).strip()
    goal = str(focus.get("goal", "")).strip()

    anchors = identity.get("anchors", {})
    room = str(anchors.get("room") or identity.get("identity", {}).get("room") or "").strip()
    email = str(
        anchors.get("contact_email") or identity.get("identity", {}).get("email") or ""
    ).strip()
    memory_kit_path = str(anchors.get("memory_kit_path", "")).strip()

    cues: List[Tuple[str, str]] = []
    day_line = _infer_day(context)
    if day_line:
        cues.append(("inferred day line", day_line))
    if goal:
        cues.append(("goal string", f"Goal: {goal}"))
    if room:
        cues.append(("room", f"Room: {room}"))
    if email:
        cues.append(("email", f"Email: {email}"))
    if memory_kit_path:
        cues.append(("memory_kit_path", f"Memory Kit Path: {memory_kit_path}"))

    return cues


def _required_do_not_repeat_topics(store: Dict[str, Dict[str, Any]]) -> List[str]:
    topics = []
    for entry in list(store["public_comms"].get("entries", [])):
        state = str(entry.get("announcement_state", "")).strip().lower()
        topic = str(entry.get("topic", "")).strip()
        if state == "do_not_repeat" and topic:
            topics.append(topic)
    return sorted(set(topics), key=lambda topic: topic.lower())


def _is_found(candidate_lower: str, expected: str) -> bool:
    return expected.strip().lower() in candidate_lower


def check_memory_candidate(data_dir: Path, candidate_path: Path) -> int:
    try:
        candidate_text = candidate_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: unable to read candidate file: {exc}")
        return 1

    store = _load_store(data_dir)
    rendered = render_lean_memory(data_dir)

    required_cues = _required_anchor_cues(store)
    required_topics = _required_do_not_repeat_topics(store)

    candidate_lower = candidate_text.lower()

    print("MEMORY CANDIDATE CHECK")
    print(f"- Candidate: {candidate_path}")
    print(f"- Candidate chars: {len(candidate_text)}")
    print(f"- Rendered chars: {len(rendered)}")

    print("- Required anchor cues:")
    all_found = True
    for label, snippet in required_cues:
        found = _is_found(candidate_lower, snippet)
        all_found = all_found and found
        status = "FOUND" if found else "MISSING"
        print(f"  * {status} | {label} | {snippet}")

    print("- Required do_not_repeat topics:")
    for topic in required_topics:
        found = _is_found(candidate_lower, topic)
        all_found = all_found and found
        status = "FOUND" if found else "MISSING"
        print(f"  * {status} | {topic}")

    print("- Reviewer reminders:")
    hard_rules = list(store["identity_constraints"].get("hard_rules", []))
    for rule in hard_rules[:5]:
        print(f"  * {rule}")

    print("- STATUS: OK" if all_found else "- STATUS: WARN")
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare a memory candidate against required cues.")
    parser.add_argument(
        "data_dir",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1] / "data"),
        help="Path to the data directory (defaults to repo data/).",
    )
    parser.add_argument("--candidate", required=True, help="Path to candidate text file.")
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir).resolve()
    candidate_path = Path(args.candidate).resolve()
    return check_memory_candidate(data_dir, candidate_path)


if __name__ == "__main__":
    raise SystemExit(main())
