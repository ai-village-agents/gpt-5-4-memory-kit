#!/usr/bin/env python3
"""Append a public communication record to public_comms.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

ALLOWED_STATES = {"announced", "do_not_repeat"}
ID_PATTERN = re.compile(r"^PC-(\d+)$")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Log a public communication record")
    parser.add_argument("data_dir", nargs="?", default=None)
    parser.add_argument("--state", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--message-summary", required=True)
    parser.add_argument("--audience", required=True)
    parser.add_argument("--date-day", required=True)
    return parser


def _is_blank(value: str) -> bool:
    return not value.strip()


def _normalized(value: str) -> str:
    return value.strip().lower()


def _parse_positive_int(value: str) -> int | None:
    try:
        parsed = int(value.strip())
    except ValueError:
        return None
    if parsed <= 0:
        return None
    return parsed


def _next_id(entries: List[Dict[str, Any]]) -> str:
    max_id = 0
    for entry in entries:
        match = ID_PATTERN.match(str(entry.get("id", "")).strip())
        if not match:
            continue
        max_id = max(max_id, int(match.group(1)))
    return f"PC-{max_id + 1}"


def _has_duplicate(entries: List[Dict[str, Any]], state: str, topic: str) -> bool:
    normalized_state = _normalized(state)
    normalized_topic = _normalized(topic)
    for entry in entries:
        entry_state = _normalized(str(entry.get("announcement_state", "")))
        entry_topic = _normalized(str(entry.get("topic", "")))
        if entry_state == normalized_state and entry_topic == normalized_topic:
            return True
    return False


def _load_optional_archive(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        archive = json.load(f)
    archive_entries = archive.get("entries", [])
    if not isinstance(archive_entries, list):
        raise ValueError("archive entries must be a list")
    return archive_entries


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv or sys.argv[1:])

    if args.data_dir:
        data_dir = Path(args.data_dir).resolve()
    else:
        data_dir = Path(__file__).resolve().parents[1] / "data"

    print("PUBLIC COMMS LOG")
    print(f"State: {args.state}")
    print(f"Topic: {args.topic}")
    print(f"Audience: {args.audience}")
    print(f"Day: {args.date_day}")

    if _is_blank(args.state):
        print("BLOCKED: --state must not be blank")
        return 1
    if _is_blank(args.topic):
        print("BLOCKED: --topic must not be blank")
        return 1
    if _is_blank(args.message_summary):
        print("BLOCKED: --message-summary must not be blank")
        return 1
    if _is_blank(args.audience):
        print("BLOCKED: --audience must not be blank")
        return 1

    day = _parse_positive_int(args.date_day)
    if day is None:
        print("BLOCKED: --date-day must be a positive integer")
        return 1

    if args.state not in ALLOWED_STATES:
        print("BLOCKED: --state must be announced or do_not_repeat")
        return 1

    public_comms_path = data_dir / "public_comms.json"
    archive_path = data_dir / "public_comms_archive.json"
    try:
        with public_comms_path.open("r", encoding="utf-8") as f:
            public_comms = json.load(f)
        archive_entries = _load_optional_archive(archive_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"BLOCKED: unable to read public-comms store ({exc})")
        return 1

    entries_obj = public_comms.get("entries", [])
    if not isinstance(entries_obj, list):
        print("BLOCKED: public_comms.json entries must be a list")
        return 1
    entries: List[Dict[str, Any]] = entries_obj
    all_entries = list(entries) + list(archive_entries)

    if _has_duplicate(all_entries, args.state, args.topic):
        print("BLOCKED: duplicate state+topic already exists")
        return 1

    new_id = _next_id(all_entries)
    entries.append(
        {
            "id": new_id,
            "announcement_state": args.state.strip(),
            "topic": args.topic.strip(),
            "message_summary": args.message_summary.strip(),
            "audience": args.audience.strip(),
            "date_day": day,
        }
    )

    with public_comms_path.open("w", encoding="utf-8") as f:
        json.dump(public_comms, f, indent=2)
        f.write("\n")

    print(f"LOGGED: {new_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
