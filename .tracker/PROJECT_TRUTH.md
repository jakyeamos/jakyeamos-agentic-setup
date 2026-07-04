---
schemaVersion: 1
projectName: jakyeamos-agent-skills
summary: Portable public skill package containing Research Domain Writing and Terrace skills, with TMCP intentionally excluded for separate release work.
healthScore: 90
statusLabel: ready
nextStep: Decide whether to keep this repo as a copyable skill pack or add a formal installer/manifest after the TMCP release model settles.
blockers: []
lastUpdated: 2026-07-04
tags: [agent-skills, codex, skills, writing, workflow-routing]
areas: [skills, documentation, validation, packaging]
goals:
  - Keep native skills portable and release-ready
  - Exclude borrowed, vendor-owned, or local-machine-only skills
  - Keep validation simple enough to run without dependencies
repoType: skill-package
sourceOfTruth: mixed
primaryLanguage: Python
activeBranch: main
lastCommitDate: "2026-07-04"
quality:
  lint: unknown
  types: unknown
  tests: pass
  coverage: pass
  package: unknown
  auditHigh: unknown
  auditModerate: unknown
  deadCode: unknown
  structure: pass
canonicalCommands:
  install: unknown
  dev: unknown
  lint: unknown
  typecheck: unknown
  test: python3 scripts/validate_skills.py
  coverage: python3 scripts/pre_cr_coverage.py
  package: unknown
  ci: pre-cr run --workspace .
  audit: unknown
  deadcode: unknown
agentExpectationsVersion: 1
lastVerifiedCommand: python3 scripts/validate_skills.py; python3 scripts/pre_cr_coverage.py; pre-cr run --workspace .
lastVerifiedAt: "2026-07-04"
---

## Current State

The repository is initialized on `main` as a small skill package. It includes:

- `skills/research-domain-writing`: an agent-first grounded writing pipeline with copied portable config, prompts, batch example, Codex metadata, and limitations notes.
- `skills/terrace`: one router skill for the Terrace CLI, with command details moved into `references/commands.md`.
- Root release hygiene files: `README.md`, `SECURITY.md`, `ATTRIBUTION.md`, `LICENSE`, `.gitignore`, `.pre-cr.json`.
- Validation support: `scripts/validate_skills.py` and `scripts/pre_cr_coverage.py`.

TMCP is intentionally excluded because the user is actively preparing TMCP separately.

## Recent Progress

- July 4: Created the initial repo and committed the package as `6ff572e` with Research Domain Writing and Terrace.
- July 4: Removed AIOS-specific RDW release notes and ran a public-package scan for private paths, local tokens, and stale npm/npx/yarn references.
- July 4: Added pre-CR configuration and trace-based LCOV generation for the skill validator so local commit hooks pass without bypassing gates.
- July 4: Created the public GitHub remote at `jakyeamos/jakyeamos-agent-skills` and pushed `main`.

## Open Problems

- No package manager metadata is present because this is a copyable skill package, not an npm/pnpm package.
- No dedicated unit-test suite exists for `scripts/validate_skills.py`; current verification is script execution plus pre-CR changed-line coverage.

## Quality Ladder Notes

- **Skill validation:** `python3 scripts/validate_skills.py` PASS.
- **Coverage adapter:** `python3 scripts/pre_cr_coverage.py` PASS and writes `.pre-cr/coverage.lcov`.
- **Pre-CR:** `pre-cr run --workspace .` PASS, with 68.5% changed-line coverage against `scripts/validate_skills.py`, threshold 0%, one covered surface file, 28 ignored surface files, zero unsupported files, and anti-slop passing.
- **Leak scan:** `rg -n "(/Users/|jakyeamos|AIOS|Vaults|Command-Center|OPENAI_API_KEY|FIRECRAWL|TOKEN|SECRET|PASSWORD|npm|npx|yarn)" ... --glob '!/.git/**'` returned no matches before the initial commit.

## Next Concrete Steps

1. Decide whether to keep this repo as a copyable skill pack or add a formal installer/manifest after the TMCP release model settles.
2. Decide whether TMCP should join this package after its portability pass.

## QR Remediation Planning

- 2026-07-04: Added GSD Phase 1 for QR remediation from qr-low-risk-post-branch-fix-20260704-jakyeamos-agent-skills; 1 plan(s) created from jakyeamos-agent-skills.md. Execution has not started.
