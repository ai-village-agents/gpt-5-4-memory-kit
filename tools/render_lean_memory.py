#!/usr/bin/env python3
"""Render a compact GPT-5.4 internal-memory candidate from memory JSON files."""

from __future__ import annotations

import json
import re
import sys
import argparse
from pathlib import Path
from typing import Any, Dict, List, Tuple

FILES = [
    "identity_constraints",
    "active_frontier",
    "settled_facts",
    "public_comms",
    "open_loops",
]

PRIORITY_RANK = {
    "high": 0,
    "medium": 1,
    "low": 2,
}

STABILITY_RANK = {
    "high": 0,
    "medium": 1,
    "low": 2,
}

PUBLIC_COMMS_STATE_RANK = {
    "do_not_repeat": 0,
    "announced": 1,
}

MAX_RENDERED_ANNOUNCED_PUBLIC_COMMS = 2


def parse_embedded_char_count(text: str) -> int | None:
    """Parse a trailing CHAR_COUNT=<n> line and return n when present."""
    match = re.search(r"(?:^|\n)CHAR_COUNT=(\d+)\n?\Z", text)
    if not match:
        return None
    return int(match.group(1))


def char_count_summary(text: str) -> Tuple[int, int | None]:
    """Return (total_chars, embedded_char_count_or_none)."""
    return len(text), parse_embedded_char_count(text)


def _humanize_label(key: str) -> str:
    parts = [part for part in re.split(r"[_-]+", key.strip()) if part]
    if not parts:
        return key
    return " ".join(part.capitalize() for part in parts)


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _infer_day(context: str) -> str | None:
    match = re.search(r"(?:^|\b)day[-_\s]?(\d+)(?:\b|$)", context, flags=re.IGNORECASE)
    if not match:
        return None
    return f"Day {match.group(1)}"


def _sorted_by_priority(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            PRIORITY_RANK.get(str(item.get("priority", "")).strip().lower(), 99),
            str(item.get("id", "")),
        ),
    )


def _sorted_facts(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            STABILITY_RANK.get(str(item.get("stability", "")).strip().lower(), 99),
            str(item.get("id", "")),
        ),
    )


def _public_comm_id_number(entry: Dict[str, Any]) -> int:
    raw_id = str(entry.get("id", "")).strip()
    match = re.search(r"(\d+)$", raw_id)
    if not match:
        return -1
    return int(match.group(1))


def _public_comm_recency_key(entry: Dict[str, Any]) -> Tuple[int, int]:
    date_day = entry.get("date_day")
    if isinstance(date_day, int):
        parsed_day = date_day
    else:
        try:
            parsed_day = int(str(date_day).strip())
        except (TypeError, ValueError):
            parsed_day = -1
    return (parsed_day, _public_comm_id_number(entry))


def _public_comms_for_render(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    do_not_repeat = []
    announced = []
    other = []

    for entry in entries:
        state = str(entry.get("announcement_state", "")).strip().lower()
        if state == "do_not_repeat":
            do_not_repeat.append(entry)
        elif state == "announced":
            announced.append(entry)
        else:
            other.append(entry)

    do_not_repeat_sorted = sorted(
        do_not_repeat,
        key=lambda entry: (_public_comm_recency_key(entry), str(entry.get("id", ""))),
    )
    announced_sorted = sorted(
        announced,
        key=lambda entry: (_public_comm_recency_key(entry), str(entry.get("id", ""))),
        reverse=True,
    )
    other_sorted = sorted(
        other,
        key=lambda entry: (
            PUBLIC_COMMS_STATE_RANK.get(
                str(entry.get("announcement_state", "")).strip().lower(),
                99,
            ),
            _public_comm_recency_key(entry),
            str(entry.get("id", "")),
        ),
    )

    rendered = do_not_repeat_sorted + announced_sorted[:MAX_RENDERED_ANNOUNCED_PUBLIC_COMMS]
    if other_sorted:
        rendered.extend(other_sorted)
    return rendered


def render_lean_memory(data_dir: Path) -> str:
    store: Dict[str, Dict[str, Any]] = {}
    for name in FILES:
        store[name] = _load_json(data_dir / f"{name}.json")

    identity = store["identity_constraints"]
    frontier = store["active_frontier"]
    settled = store["settled_facts"]
    public_comms = store["public_comms"]
    loops = store["open_loops"]

    focus = frontier.get("focus", {})
    context = str(focus.get("context", "")).strip()
    goal = str(focus.get("goal", "")).strip()

    anchors = identity.get("anchors", {})
    room = str(anchors.get("room") or identity.get("identity", {}).get("room") or "").strip()
    email = str(
        anchors.get("contact_email") or identity.get("identity", {}).get("email") or ""
    ).strip()

    lines: List[str] = []

    lines.append("Day / goal anchor")
    day_line = _infer_day(context)
    if day_line:
        lines.append(day_line)
    if goal:
        lines.append(f"Goal: {goal}")
    if context:
        lines.append(f"Context: {context}")
    lines.append("")

    lines.append("Identity / environment")
    if room:
        lines.append(f"Room: {room}")
    if email:
        lines.append(f"Email: {email}")
    if goal:
        lines.append(f"Current goal: {goal}")
    if context:
        lines.append(f"Current context: {context}")
    extra_anchor_keys = sorted(
        key for key in anchors.keys() if key not in {"room", "contact_email"}
    )
    for key in extra_anchor_keys:
        value = str(anchors.get(key, "")).strip()
        if value:
            lines.append(f"{_humanize_label(key)}: {value}")
    lines.append("")

    lines.append("Hard rules")
    hard_rules = identity.get("hard_rules", [])
    for rule in hard_rules[:5]:
        lines.append(f"- {rule}")
    lines.append("")

    lines.append("Active frontier")
    tasks = _sorted_by_priority(list(frontier.get("tasks", [])))[:3]
    for task in tasks:
        priority = str(task.get("priority", "?")).strip().lower() or "?"
        summary = str(task.get("summary", "")).strip()
        next_action = str(task.get("next_action", "")).strip()
        lines.append(f"- [{priority}] {summary} | next: {next_action}")
    lines.append("")

    lines.append("Settled facts")
    facts = _sorted_facts(list(settled.get("facts", [])))[:3]
    for fact in facts:
        statement = str(fact.get("statement", "")).strip()
        lines.append(f"- {statement}")
    lines.append("")

    lines.append("Public comms cautions")
    for entry in _public_comms_for_render(list(public_comms.get("entries", []))):
        topic = str(entry.get("topic", "")).strip()
        summary = str(entry.get("message_summary", "")).strip()
        lines.append(f"- {topic}: {summary}")
    lines.append("")

    lines.append("Open loops")
    top_loops = _sorted_by_priority(list(loops.get("loops", [])))[:3]
    for loop in top_loops:
        priority = str(loop.get("priority", "?")).strip().lower() or "?"
        question = str(loop.get("question", "")).strip()
        next_check = str(loop.get("next_check", "")).strip()
        lines.append(f"- [{priority}] {question} | next: {next_check}")

    body = "\n".join(lines).rstrip() + "\n"
    char_count = len(body)
    return f"{body}CHAR_COUNT={char_count}\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render a compact GPT-5.4 internal-memory candidate.",
    )
    parser.add_argument(
        "data_dir",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1] / "data"),
        help="Directory containing memory JSON files (default: repo data dir).",
    )
    parser.add_argument(
        "--write",
        metavar="PATH",
        help="Write rendered output to PATH instead of stdout.",
    )
    args = parser.parse_args(argv or sys.argv[1:])
    data_dir = Path(args.data_dir).resolve()
    rendered = render_lean_memory(data_dir)

    if args.write:
        destination = Path(args.write)
        destination.write_text(rendered, encoding="utf-8")
        total_chars, embedded_chars = char_count_summary(rendered)
        embedded_label = embedded_chars if embedded_chars is not None else "unknown"
        print(
            f"WROTE {destination} EMBEDDED_CHAR_COUNT={embedded_label} "
            f"TOTAL_CHAR_COUNT={total_chars}"
        )
        return 0

    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
