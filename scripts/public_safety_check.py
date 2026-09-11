#!/usr/bin/env python3
"""Scan public workbench files for private paths and credential material."""

from __future__ import annotations

import argparse
import json
import subprocess
import re
from pathlib import Path
from typing import Iterable

IGNORED_DIRECTORIES = {
    ".aios",
    ".git",
    ".pre-cr",
    ".planning",
    ".quality-runner",
    ".tmcp",
    "__pycache__",
    ".venv",
    "node_modules",
    "audit",
    ".agent-config-state",
}
INTENTIONAL_RULE_FILES = {
    "scripts/catalog_validation.py",
    "scripts/public_safety_check.py",
    "scripts/validate_skills.py",
}
PRIVATE_PATH_PATTERNS = (
    re.compile(
        r"(?<![A-Za-z0-9_])/(?:Users|home|private/var|var/folders)/[^\s'\"`<>]+"
    ),
    re.compile(r"(?<![A-Za-z0-9_])~/[^\s'\"`<>]+"),
)
AUTHORIZATION_PATTERN = re.compile(
    r"(?i)(?:authorization|proxy-authorization)\s*:\s*(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"
)
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|token)\s*[=:]\s*[\"']?[A-Za-z0-9_./+=-]{12,}"
)
KNOWN_TOKEN_PATTERN = re.compile(
    r"\b(?:sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{16,}|AIza[A-Za-z0-9_-]{20,})\b"
)
PRIVATE_DATABASE_PATTERN = re.compile(
    r"(?i)\b(?:session|transcript|credentials|auth)(?:[-_][A-Za-z0-9.-]+)?\.(?:db|sqlite|log)\b"
)


def _is_ignored(path: Path, root: Path) -> bool:
    relative_parts = path.relative_to(root).parts
    return any(part in IGNORED_DIRECTORIES for part in relative_parts)


def _is_local_compass_receipt(path: Path, root: Path) -> bool:
    """Only Git-ignored, untracked producer receipts are local runtime data."""
    relative = path.relative_to(root).as_posix()
    if not relative.startswith(".project-compass/evidence/") or path.is_symlink():
        return False
    try:
        if path.stat().st_size > 1_048_576:
            return False
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema") != "compass-evidence/v1":
            return False
        # check-ignore never accepts tracked files, including force-added receipts.
        result = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-q", "--", relative],
            capture_output=True, timeout=5, check=False,
        )
        return result.returncode == 0
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False


def public_files(root: Path) -> Iterable[Path]:
    """Yield public files while excluding generated and local runtime trees."""

    for path in sorted(root.rglob("*")):
        if not path.is_file() or _is_ignored(path, root) or _is_local_compass_receipt(path, root):
            continue
        relative = path.relative_to(root).as_posix()
        if relative in INTENTIONAL_RULE_FILES:
            continue
        if path.name == ".env" or path.name.startswith(".env"):
            yield path
            continue
        yield path


def scan_text(path: Path, text: str) -> list[str]:
    """Return line-level safety findings for one text file."""

    findings: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        patterns = (
            (PRIVATE_PATH_PATTERNS[0], "private absolute path"),
            (PRIVATE_PATH_PATTERNS[1], "private home path"),
            (AUTHORIZATION_PATTERN, "raw authorization header"),
            (SECRET_ASSIGNMENT_PATTERN, "secret-like assignment"),
            (KNOWN_TOKEN_PATTERN, "known credential format"),
            (PRIVATE_DATABASE_PATTERN, "private session or credential artifact"),
        )
        for pattern, description in patterns:
            if pattern.search(line):
                findings.append(f"{path}:{line_number}: {description}")
    return findings


def scan_repository(root: Path) -> list[str]:
    """Return public-safety findings for a repository root."""

    findings: list[str] = []
    for path in public_files(root):
        relative = path.relative_to(root).as_posix()
        if path.name == ".env" or path.name.startswith(".env"):
            findings.append(f"{relative}: environment file is not distributable")
            continue
        if path.suffix.lower() in {".pem", ".key"} or path.name in {
            "id_rsa",
            "credentials.json",
        }:
            findings.append(f"{relative}: credential-bearing file is not distributable")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend(scan_text(Path(relative), text))
    return findings


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the public-safety scan."""

    args = _parser().parse_args(argv)
    findings = scan_repository(args.root.resolve())
    if args.json:
        import json

        print(
            json.dumps(
                {"findings": findings, "ok": not findings}, indent=2, sort_keys=True
            )
        )
    else:
        if findings:
            for finding in findings:
                print(finding)
        else:
            print("public safety ok")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
