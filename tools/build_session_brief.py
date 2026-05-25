#!/usr/bin/env python3
"""Build a compact session brief from memory store JSON files."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

try:
    from tools.render_lean_memory import _public_comms_for_render
except ModuleNotFoundError:
    from render_lean_memory import _public_comms_for_render

ORDER = [
    "identity_constraints",
    "active_frontier",
    "settled_facts",
    "public_comms",
    "open_loops",
]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_brief(data_dir: Path) -> str:
    store: Dict[str, Dict[str, Any]] = {}
    for name in ORDER:
        store[name] = _load_json(data_dir / f"{name}.json")

    identity = store["identity_constraints"]
    frontier = store["active_frontier"]
    settled = store["settled_facts"]
    comms = store["public_comms"]
    loops = store["open_loops"]

    lines = []
    lines.append("SESSION BRIEF")
    lines.append("")

    lines.append("1) identity_constraints")
    for rule in identity.get("hard_rules", [])[:3]:
        lines.append(f"- {rule}")
    anchors = identity.get("anchors", {})
    if anchors:
        room = anchors.get("room", "unknown")
        email = anchors.get("contact_email", "unknown")
        lines.append(f"- Anchors: room={room}; email={email}")
    lines.append("")

    lines.append("2) active_frontier")
    focus = frontier.get("focus", {})
    goal = focus.get("goal", "(no goal set)")
    context = focus.get("context", "(no context)")
    lines.append(f"- Context: {context}")
    lines.append(f"- Goal: {goal}")
    for task in frontier.get("tasks", [])[:3]:
        lines.append(
            f"- [{task.get('priority', '?')}] {task.get('summary', '')} -> {task.get('next_action', '')}"
        )
    dnr = frontier.get("high_priority_do_not_repeat", [])
    if dnr:
        lines.append("- HIGH PRIORITY DO-NOT-REPEAT:")
        for item in dnr[:4]:
            lines.append(f"  * {item}")
    lines.append("")

    lines.append("3) settled_facts")
    for fact in settled.get("facts", [])[:4]:
        lines.append(f"- {fact.get('statement', '')}")
    lines.append("")

    lines.append("4) public_comms")
    for entry in _public_comms_for_render(list(comms.get("entries", []))):
        state = entry.get("announcement_state", "unknown")
        topic = entry.get("topic", "")
        msg = entry.get("message_summary", "")
        lines.append(f"- [{state}] {topic}: {msg}")
    lines.append("")

    lines.append("5) open_loops")
    open_items = sorted(
        loops.get("loops", []),
        key=lambda x: 0 if str(x.get("priority", "")).lower() == "high" else 1,
    )
    for item in open_items[:5]:
        lines.append(
            f"- [{item.get('priority', '?')}] {item.get('question', '')} -> {item.get('next_check', '')}"
        )

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if argv:
        data_dir = Path(argv[0]).resolve()
    else:
        data_dir = Path(__file__).resolve().parents[1] / "data"

    brief = build_brief(data_dir)
    print(brief, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
