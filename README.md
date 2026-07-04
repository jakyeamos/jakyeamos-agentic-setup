# Jakye Amos Agent Skills

Portable agent skills for grounded writing and workflow routing.

This repository currently includes:

- `research-domain-writing` - a research -> packet -> draft -> QA -> style pipeline for domain-specific writing.
- `terrace` - a single router skill for the Terrace workflow CLI.

TMCP is intentionally not included in this repo yet. It is being prepared separately.

## Install

Copy a skill folder into an agent skill directory, for example:

```bash
mkdir -p ~/.agents/skills
cp -R skills/research-domain-writing ~/.agents/skills/research-domain-writing
cp -R skills/terrace ~/.agents/skills/terrace
```

For Codex, any supported skill root containing a `SKILL.md` should work. Restart the agent session after copying skills so metadata is reloaded.

## Skills

### Research Domain Writing

Use when copy needs factual grounding, domain terminology, source notes, and QA before styling.

Example request:

```text
Use $research-domain-writing to improve the copy on my LIS leaderboard for fantasy basketball users.
```

### Terrace

Use when a project is managed by the Terrace CLI and the agent needs to route planning, execution, validation, review, or release-readiness work through Terrace.

Example request:

```text
Use $terrace to plan and execute the next phase.
```

## Validation

Run:

```bash
python3 scripts/validate_skills.py
```

The validator checks required skill files, frontmatter shape, basic local links, and accidental private-path leaks.

## Release Notes

This package is intentionally small. Borrowed/vendor skills and personal-machine wrappers are excluded.
