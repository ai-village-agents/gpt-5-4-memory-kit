#!/usr/bin/env python3
"""Prune older announced public_comms entries into an archive file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

try:
    from render_lean_memory import _public_comm_recency_key
except ImportError:
    from tools.render_lean_memory import _public_comm_recency_key


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prune older announced public_comms entries into an archive file."
    )
    parser.add_argument("data_dir", nargs="?", default=None)
    parser.add_argument("--keep-announced", type=int, default=2)
    parser.add_argument("--archive", default=None)
    return parser


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")


def _archive_template(last_updated: str) -> Dict[str, Any]:
    return {
        "schema": "memory-kit/v1",
        "memory_type": "public_comms_archive",
        "last_updated": last_updated,
        "entries": [],
    }


def _announced_to_archive(
    entries: List[Dict[str, Any]],
    keep_announced: int,
) -> Set[str]:
    announced = [
        entry
        for entry in entries
        if str(entry.get("announcement_state", "")).strip().lower() == "announced"
    ]
    announced_sorted = sorted(
        announced,
        key=lambda entry: (_public_comm_recency_key(entry), str(entry.get("id", ""))),
        reverse=True,
    )
    kept_ids = {
        str(entry.get("id", ""))
        for entry in announced_sorted[:keep_announced]
        if str(entry.get("id", ""))
    }
    return {
        str(entry.get("id", ""))
        for entry in announced
        if str(entry.get("id", "")) and str(entry.get("id", "")) not in kept_ids
    }


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv or sys.argv[1:])

    if args.keep_announced < 0:
        print("BLOCKED: --keep-announced must be >= 0")
        return 1

    if args.data_dir:
        data_dir = Path(args.data_dir).resolve()
    else:
        data_dir = Path(__file__).resolve().parents[1] / "data"

    public_comms_path = data_dir / "public_comms.json"
    archive_path = Path(args.archive).resolve() if args.archive else data_dir / "public_comms_archive.json"

    try:
        public_comms = _load_json(public_comms_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: unable to read public_comms.json ({exc})")
        return 1

    entries_obj = public_comms.get("entries", [])
    if not isinstance(entries_obj, list):
        print("BLOCKED: public_comms.json entries must be a list")
        return 1
    active_entries: List[Dict[str, Any]] = entries_obj

    archive_last_updated = str(public_comms.get("last_updated", "")).strip()
    if archive_path.exists():
        try:
            archive = _load_json(archive_path)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"BLOCKED: unable to read archive file ({exc})")
            return 1
    else:
        archive = _archive_template(archive_last_updated)

    archive_entries_obj = archive.get("entries", [])
    if not isinstance(archive_entries_obj, list):
        print("BLOCKED: archive entries must be a list")
        return 1
    archive_entries: List[Dict[str, Any]] = archive_entries_obj

    archive_ids = {str(entry.get("id", "")) for entry in archive_entries if str(entry.get("id", ""))}
    announced_archive_ids = _announced_to_archive(active_entries, args.keep_announced)

    new_archived_entries: List[Dict[str, Any]] = []
    for entry in active_entries:
        entry_id = str(entry.get("id", ""))
        if entry_id and entry_id in announced_archive_ids and entry_id not in archive_ids:
            new_archived_entries.append(entry)

    if new_archived_entries:
        archive_entries.extend(new_archived_entries)

    active_entries_pruned = []
    for entry in active_entries:
        entry_id = str(entry.get("id", ""))
        if entry_id and entry_id in announced_archive_ids:
            continue
        active_entries_pruned.append(entry)

    public_comms["entries"] = active_entries_pruned
    archive["entries"] = archive_entries

    _write_json(public_comms_path, public_comms)
    _write_json(archive_path, archive)

    kept_announced_count = sum(
        1
        for entry in active_entries_pruned
        if str(entry.get("announcement_state", "")).strip().lower() == "announced"
    )
    archived_this_run_count = len(new_archived_entries)
    status = "OK" if archived_this_run_count > 0 else "NO-OP"

    print("PRUNE-PUBLIC-COMMS")
    print(f"ACTIVE: {public_comms_path}")
    print(f"ARCHIVE: {archive_path}")
    print(f"KEPT_ANNOUNCED: {kept_announced_count}")
    print(f"ARCHIVED_THIS_RUN: {archived_this_run_count}")
    print(f"ACTIVE_TOTAL: {len(active_entries_pruned)}")
    print(f"ARCHIVE_TOTAL: {len(archive_entries)}")
    print(f"STATUS: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
