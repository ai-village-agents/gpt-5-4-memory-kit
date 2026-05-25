#!/usr/bin/env python3
"""Run a pre-send check for public chat messages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

VAGUE_DUPLICATE_CHECK_VALUES = {
    "checked",
    "ok",
    "looks good",
    "none",
    "n/a",
    "na",
    "no duplicate",
}


def _load_public_comms(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run pre-send public chat checks")
    parser.add_argument("data_dir", nargs="?", default=None)
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--recipient", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--duplicate-check", required=True)
    return parser


def _is_blank(value: str) -> bool:
    return not value.strip()


def _is_vague_duplicate_check(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in VAGUE_DUPLICATE_CHECK_VALUES:
        return True
    return len(value.strip()) < 12


def _do_not_repeat_lines(entries: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for entry in entries:
        state = str(entry.get("announcement_state", "")).strip().lower()
        if state != "do_not_repeat":
            continue
        entry_id = str(entry.get("id", "<unknown>"))
        topic = str(entry.get("topic", "")).strip() or "<no topic>"
        lines.append(f"- {entry_id}: {topic}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv or sys.argv[1:])

    if args.data_dir:
        data_dir = Path(args.data_dir).resolve()
    else:
        data_dir = Path(__file__).resolve().parents[1] / "data"

    public_comms_path = data_dir / "public_comms.json"

    try:
        public_comms = _load_public_comms(public_comms_path)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: unable to read public_comms.json ({exc})")
        return 1

    print("PRE-SEND CHAT CHECK")
    print(f"- Purpose: {args.purpose}")
    print(f"- Recipient: {args.recipient}")
    print(f"- Topic: {args.topic}")
    print(f"- Duplicate-check: {args.duplicate_check}")
    print("- Current do_not_repeat public-comms entries:")

    lines = _do_not_repeat_lines(public_comms.get("entries", []))
    if lines:
        for line in lines:
            print(line)
    else:
        print("- none")

    required_fields = {
        "purpose": args.purpose,
        "recipient": args.recipient,
        "topic": args.topic,
        "duplicate-check": args.duplicate_check,
    }
    for field, value in required_fields.items():
        if _is_blank(value):
            print(f"BLOCKED: --{field} must not be blank")
            return 1

    if _is_vague_duplicate_check(args.duplicate_check):
        print("BLOCKED: --duplicate-check is too vague; provide specific evidence")
        return 1

    print("READY: compare visible events against public_comms before sending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
