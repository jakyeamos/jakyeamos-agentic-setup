#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
PRIVATE_PATH_PATTERNS = (
    "~/.ssh",
    ".env",
)
PRIVATE_PATH_REGEXES = (
    re.compile(r"/" + r"Users/" + r"[^\s)'\"`]+"),
)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError("missing YAML frontmatter")
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    return data


def markdown_links(text: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_dir}: missing SKILL.md"]

    try:
        frontmatter = parse_frontmatter(skill_md)
    except ValueError as exc:
        errors.append(f"{skill_md}: {exc}")
        frontmatter = {}

    if not frontmatter.get("name"):
        errors.append(f"{skill_md}: missing name")
    if not frontmatter.get("description"):
        errors.append(f"{skill_md}: missing description")

    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(errors="replace")
        for pattern in PRIVATE_PATH_PATTERNS:
            if pattern in text:
                errors.append(f"{path}: contains private path/token pattern {pattern!r}")
        for pattern in PRIVATE_PATH_REGEXES:
            if pattern.search(text):
                errors.append(f"{path}: contains private path pattern {pattern.pattern!r}")
        if path.suffix.lower() == ".md":
            for target in markdown_links(text):
                if re.match(r"^[a-z]+://|^mailto:|^#", target):
                    continue
                target_path = (path.parent / target.split("#", 1)[0]).resolve()
                if not target_path.exists():
                    errors.append(f"{path}: broken local link {target}")
    return errors


def main() -> int:
    errors: list[str] = []
    for skill_dir in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        errors.extend(validate_skill(skill_dir))
    if errors:
        for error in errors:
            print(error)
        return 1
    print("skill validation ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
