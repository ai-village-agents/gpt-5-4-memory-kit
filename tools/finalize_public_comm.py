#!/usr/bin/env python3
"""Log a public communication entry, then prune public_comms in one command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import log_public_comm
    import prune_public_comms
else:
    from . import log_public_comm, prune_public_comms


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Log a public communication entry and prune announced history.",
    )
    parser.add_argument("data_dir", nargs="?", default=None)
    parser.add_argument("--state", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--message-summary", required=True)
    parser.add_argument("--audience", required=True)
    parser.add_argument("--date-day", required=True)
    parser.add_argument("--keep-announced", type=int, default=2)
    parser.add_argument("--archive", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv or sys.argv[1:])

    if args.data_dir:
        data_dir = Path(args.data_dir).resolve()
    else:
        data_dir = Path(__file__).resolve().parents[1] / "data"

    print("FINALIZE-PUBLIC-COMM")

    log_args = [
        str(data_dir),
        "--state",
        args.state,
        "--topic",
        args.topic,
        "--message-summary",
        args.message_summary,
        "--audience",
        args.audience,
        "--date-day",
        args.date_day,
    ]
    log_rc = log_public_comm.main(log_args)
    if log_rc != 0:
        return log_rc

    prune_args = [str(data_dir), "--keep-announced", str(args.keep_announced)]
    if args.archive:
        prune_args.extend(["--archive", args.archive])

    prune_rc = prune_public_comms.main(prune_args)
    if prune_rc != 0:
        return prune_rc

    print("FINALIZED: logged and pruned public_comms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
