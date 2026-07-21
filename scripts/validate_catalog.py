#!/usr/bin/env python3
"""Standalone entrypoint for catalog validation."""

from __future__ import annotations

from pathlib import Path

try:
    from .catalog_validation import validate_manifest
except ImportError:
    from catalog_validation import validate_manifest


def main() -> int:
    """Validate the catalog in the current checkout."""

    root = Path(__file__).resolve().parents[1]
    errors = validate_manifest(root)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("catalog validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
