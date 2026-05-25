#!/usr/bin/env python3
"""Run the practical session-start routine for the memory kit."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from audit_memory_store import audit_store
    from build_session_brief import build_brief
    from validate_inventory import load_inventory, validate_inventory
else:
    from .audit_memory_store import audit_store
    from .build_session_brief import build_brief
    from .validate_inventory import load_inventory, validate_inventory


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if argv:
        data_dir = Path(argv[0]).resolve()
    else:
        data_dir = Path(__file__).resolve().parents[1] / "data"

    errors, warnings = audit_store(data_dir)

    if errors:
        print("SESSION START BLOCKED: fix memory-store errors first.")
        print()
        for err in errors:
            print(f"- {err}")
        return 1

    print(build_brief(data_dir), end="")
    print()
    print("SESSION START CHECK")
    if warnings:
        print("- Audit status: warnings present")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("- Audit status: OK")

    inventory_path = data_dir.parent / "inventory.yaml"
    if not inventory_path.exists():
        print("- Inventory status: skipped (inventory.yaml not found)")
    else:
        try:
            inventory_data = load_inventory(inventory_path)
        except (OSError, ValueError) as exc:
            inventory_errors = [f"unable to read inventory: {exc}"]
        else:
            inventory_errors = validate_inventory(inventory_data, data_dir.parent)

        if inventory_errors:
            print("- Inventory status: warnings/errors present")
            for error in inventory_errors:
                line = error[2:] if error.startswith("- ") else error
                print(f"- {line}")
        else:
            print("- Inventory status: OK")

    print("- Suggested first move: act from active_frontier, not from full history.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
