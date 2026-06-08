#!/usr/bin/env python3
"""Compare GitHub contents API visibility with raw.githubusercontent.com visibility."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


@dataclass
class ContentsResult:
    status: str  # present | missing | error
    sha: str | None
    size: int | None
    error: str | None


@dataclass
class RawResult:
    http_status: int | None
    size: int | None
    error: str | None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare GitHub contents API visibility with raw visibility for one file."
    )
    parser.add_argument("--repo", required=True, help="Repository in owner/name form.")
    parser.add_argument("--path", required=True, help="File path in the repository.")
    parser.add_argument("--ref", default="main", help="Git ref (default: main).")
    parser.add_argument(
        "--raw-base-url",
        default="https://raw.githubusercontent.com",
        help="Override raw base URL (default: https://raw.githubusercontent.com).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="HTTP timeout in seconds (default: 20).",
    )
    return parser.parse_args(argv)


def _is_404_output(text: str) -> bool:
    t = text.lower()
    return "404" in t or "not found" in t


def fetch_contents(repo: str, path: str, ref: str, timeout: float) -> tuple[ContentsResult, bool]:
    encoded_path = quote(path, safe="/")
    encoded_ref = quote(ref, safe="")
    endpoint = f"repos/{repo}/contents/{encoded_path}?ref={encoded_ref}"

    try:
        cp = subprocess.run(
            ["gh", "api", "--method", "GET", endpoint],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return ContentsResult("error", None, None, "gh CLI not found"), True
    except subprocess.TimeoutExpired:
        return ContentsResult("error", None, None, "gh api timed out"), True
    except OSError as exc:
        return ContentsResult("error", None, None, f"gh api failed: {exc}"), True

    merged = f"{cp.stdout}\n{cp.stderr}".strip()
    if cp.returncode == 0:
        try:
            payload: Any = json.loads(cp.stdout)
        except json.JSONDecodeError:
            return ContentsResult("error", None, None, "invalid JSON from gh api"), True
        sha = payload.get("sha") if isinstance(payload, dict) else None
        size = payload.get("size") if isinstance(payload, dict) else None
        sha_str = str(sha) if isinstance(sha, str) and sha else None
        size_int = size if isinstance(size, int) else None
        return ContentsResult("present", sha_str, size_int, None), False

    if _is_404_output(merged):
        return ContentsResult("missing", None, None, None), False

    err = merged if merged else f"gh api exit code {cp.returncode}"
    return ContentsResult("error", None, None, err), True


def fetch_raw(raw_url: str, timeout: float) -> tuple[RawResult, bool]:
    req = Request(raw_url, method="GET")
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            status = getattr(resp, "status", 200)
            return RawResult(int(status), len(data), None), False
    except HTTPError as exc:
        # Treat 404 as a normal comparison outcome, not a runtime failure.
        if exc.code == 404:
            return RawResult(404, None, None), False
        return RawResult(exc.code, None, f"HTTPError {exc.code}"), True
    except URLError as exc:
        return RawResult(None, None, f"URLError: {exc.reason}"), True
    except TimeoutError:
        return RawResult(None, None, "timeout"), True
    except OSError as exc:
        return RawResult(None, None, f"raw fetch failed: {exc}"), True


def choose_interpretation(contents: ContentsResult, raw: RawResult, had_failure: bool) -> str:
    if had_failure or contents.status == "error":
        return "ERROR"
    raw_present = raw.http_status == 200
    raw_missing = raw.http_status == 404

    if contents.status == "present" and raw_present:
        return "MATCH"
    if contents.status == "present" and raw_missing:
        return "RAW_LAG_OR_CACHE"
    if contents.status == "missing" and raw_present:
        return "CONTENTS_MISSING_RAW_PRESENT"
    if contents.status == "missing" and raw_missing:
        return "BOTH_MISSING"
    return "ERROR"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    raw_base = args.raw_base_url.rstrip("/")
    raw_path = quote(args.path, safe="/")
    raw_url = f"{raw_base}/{args.repo}/{quote(args.ref, safe='')}/{raw_path}"

    contents, contents_failed = fetch_contents(args.repo, args.path, args.ref, args.timeout)
    raw, raw_failed = fetch_raw(raw_url, args.timeout)

    had_failure = contents_failed or raw_failed
    interpretation = choose_interpretation(contents, raw, had_failure)

    print("GITHUB RAW GAP CHECK")
    print(f"repo: {args.repo}")
    print(f"path: {args.path}")
    print(f"ref: {args.ref}")
    print(f"contents_api_status: {contents.status}")
    print(f"raw_url: {raw_url}")
    print(f"raw_http_status: {raw.http_status if raw.http_status is not None else 'n/a'}")
    print(f"content_size: {raw.size if raw.size is not None else contents.size if contents.size is not None else 'n/a'}")
    print(f"contents_sha: {contents.sha if contents.sha else 'n/a'}")
    print(f"interpretation: {interpretation}")

    if contents.error:
        print(f"details: contents_error={contents.error}")
    if raw.error:
        print(f"details: raw_error={raw.error}")

    return 1 if interpretation == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
