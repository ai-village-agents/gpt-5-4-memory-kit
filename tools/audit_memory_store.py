#!/usr/bin/env python3
"""Validate memory store JSON files and warn about bloat/drift."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REQUIRED_KEYS = {
    "identity_constraints": ["schema", "memory_type", "principles", "hard_rules", "anchors", "do_not_store"],
    "active_frontier": ["schema", "memory_type", "focus", "tasks", "high_priority_do_not_repeat"],
    "settled_facts": ["schema", "memory_type", "facts", "anti_patterns"],
    "public_comms": ["schema", "memory_type", "entries"],
    "open_loops": ["schema", "memory_type", "loops", "parking_lot"],
}

LIST_LIMITS = {
    "identity_constraints.principles": 8,
    "identity_constraints.hard_rules": 8,
    "active_frontier.tasks": 7,
    "active_frontier.high_priority_do_not_repeat": 6,
    "settled_facts.facts": 20,
    "public_comms.entries": 25,
    "open_loops.loops": 10,
}

ANNOUNCEMENT_STATES = {"announced", "do_not_repeat"}


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _text_has_settled_signal(text: str) -> bool:
    text = text.lower()
    tokens = ["always", "never", "confirmed", "settled", "stable", "known pattern"]
    return any(token in text for token in tokens)


def _text_has_open_signal(text: str) -> bool:
    text = text.lower()
    tokens = ["todo", "investigate", "need to", "should ", "next action", "open question", "plan"]
    return any(token in text for token in tokens)


def _check_list_limit(name: str, data: Dict[str, Any], key: str, limit: int, warnings: List[str]) -> None:
    value = data.get(key)
    if isinstance(value, list) and len(value) > limit:
        warnings.append(f"{name}.{key} has {len(value)} items (recommended <= {limit})")


def audit_store(data_dir: Path) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    loaded: Dict[str, Dict[str, Any]] = {}

    for name, required in REQUIRED_KEYS.items():
        path = data_dir / f"{name}.json"
        if not path.exists():
            errors.append(f"missing file: {path.name}")
            continue
        try:
            obj = _load_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid json in {path.name}: {exc}")
            continue

        loaded[name] = obj
        for key in required:
            if key not in obj:
                errors.append(f"{path.name} missing required key: {key}")

    if errors:
        return errors, warnings

    for key_path, limit in LIST_LIMITS.items():
        file_key, list_key = key_path.split(".", 1)
        _check_list_limit(file_key, loaded[file_key], list_key, limit, warnings)

    active_tasks = loaded["active_frontier"].get("tasks", [])
    for item in active_tasks:
        blob = " ".join(
            [str(item.get("summary", "")), str(item.get("next_action", "")), str(item.get("status", ""))]
        )
        if _text_has_settled_signal(blob) and str(item.get("status", "")).lower() in {"done", "completed"}:
            warnings.append(
                f"active_frontier task {item.get('id', '<unknown>')} looks like a settled fact; consider moving to settled_facts"
            )

    settled_items = loaded["settled_facts"].get("facts", [])
    for fact in settled_items:
        stmt = str(fact.get("statement", ""))
        if _text_has_open_signal(stmt):
            warnings.append(
                f"settled_facts item {fact.get('id', '<unknown>')} looks unresolved; consider moving to open_loops/active_frontier"
            )

    entries = loaded["public_comms"].get("entries", [])
    for entry in entries:
        state = str(entry.get("announcement_state", "")).strip().lower()
        if state not in ANNOUNCEMENT_STATES:
            warnings.append(
                f"public_comms entry {entry.get('id', '<unknown>')} missing clear announcement_state (announced or do_not_repeat)"
            )

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if argv:
        data_dir = Path(argv[0]).resolve()
    else:
        data_dir = Path(__file__).resolve().parents[1] / "data"

    errors, warnings = audit_store(data_dir)

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"- {e}")

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"- {w}")

    if not errors and not warnings:
        print("Memory store audit: OK")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
