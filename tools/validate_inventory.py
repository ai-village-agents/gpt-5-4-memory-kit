#!/usr/bin/env python3
"""Validate inventory.yaml for required shared metadata fields."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

REQUIRED_FIELDS = ("id", "status", "kind", "summary", "source", "last_verified", "retrieval_cue")
REPO_ROOT = Path(__file__).resolve().parents[1]


def _parse_simple_inventory_yaml(text: str) -> List[Dict[str, str]]:
    """Parse the repo's flat list-of-maps YAML format without external deps."""
    items: List[Dict[str, str]] = []
    current: Dict[str, str] | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line.startswith("- "):
            if current is not None:
                items.append(current)
            current = {}
            stripped = line[2:].strip()
            if stripped:
                key, sep, value = stripped.partition(":")
                if not sep:
                    raise ValueError(f"invalid list item line: {raw_line}")
                current[key.strip()] = value.strip()
            continue

        if current is None:
            raise ValueError("top-level must be a list")

        if ":" not in stripped:
            raise ValueError(f"invalid mapping line: {raw_line}")
        key, value = stripped.split(":", 1)
        current[key.strip()] = value.strip()

    if current is not None:
        items.append(current)

    return items


def load_inventory(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        return _parse_simple_inventory_yaml(text)
    return yaml.safe_load(text)


def _is_relative_file_path(value: str) -> bool:
    return "://" not in value and not value.startswith("~") and not Path(value).is_absolute()


def validate_inventory(data: Any, repo_root: Path) -> List[str]:
    errors: List[str] = []

    if not isinstance(data, list):
        return ["top-level must be a non-empty list"]
    if not data:
        return ["top-level must be a non-empty list"]

    seen_ids: set[str] = set()
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            errors.append(f"- item {index} must be a mapping")
            continue

        for field in REQUIRED_FIELDS:
            value = item.get(field)
            if value is None or not str(value).strip():
                errors.append(f"- item {index} missing non-blank field: {field}")

        raw_id = str(item.get("id", "")).strip()
        if raw_id:
            if raw_id in seen_ids:
                errors.append(f"- duplicate id: {raw_id}")
            seen_ids.add(raw_id)

        source = str(item.get("source", "")).strip()
        if source and _is_relative_file_path(source):
            if not (repo_root / source).exists():
                errors.append(f"- source file not found: {source}")

    return errors


def main(argv: List[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    inventory_path = Path(argv[0]).resolve() if argv else (REPO_ROOT / "inventory.yaml")

    print("INVENTORY CHECK")

    try:
        data = load_inventory(inventory_path)
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"- unable to read inventory: {exc}")
        print("STATUS: ERROR")
        return 1

    errors = validate_inventory(data, REPO_ROOT)
    if errors:
        for error in sorted(errors):
            print(error)
        print("STATUS: ERROR")
        return 1

    print(f"Items: {len(data)}")
    print("STATUS: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
