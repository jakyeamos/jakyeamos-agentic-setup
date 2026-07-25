#!/usr/bin/env python3
"""Run the public catalog validators as one deterministic quality gate."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.catalog_validation import validate_manifest  # noqa: E402
from scripts.public_safety_check import scan_repository  # noqa: E402
from scripts.validate_prevention_pack import validate_prevention_pack  # noqa: E402
from scripts.validate_skills import validate_skill  # noqa: E402


def validate_repository(root: Path = ROOT) -> list[str]:
    """Return all public catalog validation findings in stable order."""

    errors = list(validate_manifest(root))
    errors.extend(f"public safety: {finding}" for finding in scan_repository(root))
    errors.extend(validate_prevention_pack(root))
    skills_root = root / "skills"
    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        errors.extend(validate_skill(skill_dir))
    return sorted(set(errors))


def main() -> int:
    """Run the complete repository validator."""

    errors = validate_repository()
    if errors:
        print("\n".join(errors))
        return 1
    print("repository validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
