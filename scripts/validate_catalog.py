#!/usr/bin/env python3
"""Standalone entrypoint for catalog validation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if not __package__:
    sys.path.insert(0, str(ROOT))

# Direct script execution bootstraps the repository root before this import.
from scripts.catalog_validation import validate_manifest  # noqa: E402


def main() -> int:
    """Validate the catalog in the current checkout."""

    errors = validate_manifest(ROOT)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("catalog validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
