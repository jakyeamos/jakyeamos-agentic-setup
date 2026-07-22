---
schemaVersion: 1
projectName: jakyeamos-agent-skills
summary: Portable Agentic Workbench cataloging reusable context, routing, safety, evaluation, handoff, environment-legibility, and durable execution workflows with eleven portable skills.
healthScore: 94
statusLabel: ready
nextStep: Complete the final cross-repository status review for the additive v0.3.0 catalog; no publish, tag, or push is authorized in this pass.
blockers: []
lastUpdated: 2026-07-22
tags: [agent-skills, portable-workbench, context-management, workflow-routing, safety, evaluation]
areas: [catalog, installer, workflows, adapters, documentation, validation]
goals:
  - Keep native Research Domain Writing and Terrace skills portable and backward-compatible
  - Make catalog provenance, evidence, targets, dependencies, and installation mode agent-minable
  - Keep private runtime infrastructure, generated harvests, credentials, and managed vendor files outside the public boundary
  - Keep validation simple enough to run without external dependencies
  - Keep the public catalog canonical for portable redistribution while preserving AIOS as an internal archival/runtime reference
repoType: portable-agent-workbench
sourceOfTruth: catalog/manifest.json
primaryLanguage: Python
integrationBranch: dev
activeBranch: dev
lastCommitDate: "2026-07-22"
quality:
  lint: pass
  types: warning
  tests: pass
  coverage: pass
  package: pass
  auditHigh: pass
  auditModerate: pass
  deadCode: pass
  structure: pass
canonicalCommands:
  install: python3 scripts/workbench.py install <asset-id> --target <target> --root <explicit-root> --dry-run
  dev: unknown
  lint: ruff check scripts tests
  typecheck: basedpyright scripts tests
  test: python3 -m unittest discover -s tests -p 'test_*.py'
  coverage: python3 scripts/pre_cr_coverage.py
  package: python3 scripts/workbench.py validate
  ci: pre-cr run --workspace .
  audit: python3 scripts/public_safety_check.py
  deadcode: vulture scripts tests --min-confidence 70
agentExpectationsVersion: 1
lastVerifiedCommand: python3 scripts/validate_skills.py; python3 scripts/validate_catalog.py; python3 scripts/public_safety_check.py; python3 scripts/workbench.py validate; python3 -m unittest discover -s tests -p 'test_*.py'
lastVerifiedAt: "2026-07-22"
---

## Current State

The repository is now a public Portable Agentic Workbench catalog. The
authoritative `catalog/manifest.json` is version `0.3.0` and records eleven
portable skills, portable workflows, staged adapters, external references,
evidence, provenance, and safe installation. The dependency-free Python CLI
supports deterministic list, search, show, install, and validate commands.
The original skill paths remain unchanged, and the nine additive skills have
trigger/non-trigger forward cases plus clean-room package fixtures. The
environment-legibility workflow continues to document the offline bootstrap
outcome taxonomy used by the leverage audit.

Commit `1762727` contains the additive mining release. The current work is
additive and does not execute or rewrite the existing QR-remediation phase.
Commit `f5389ac` folds the mined durable-work, change-surface, claim-evidence,
and instruction-routing boundaries into the existing public workflows instead
of leaving overlapping guidance as duplicate surfaces.

## Recent Progress

- 2026-07-21: Added the versioned catalog, source classes, portable workflows,
  staged vendor adapters, external reference records, and case studies.
- 2026-07-21: Added the standard-library catalog CLI, catalog validator, public
  safety scanner, clean-room installer tests, and coverage adapter.
- 2026-07-21: Committed the catalog and installer implementation as
  `50f74ea` after a non-empty-diff Pre-CR PASS.
- 2026-07-21: Extended the trace coverage adapter and changed-line surface as
  `342f8b6` with another Pre-CR PASS.
- 2026-07-21: Published the human mining guide, case studies, portable
  workflows, staged adapters, and CI validation as `f210835`.
- 2026-07-21: Recorded the additive Phase 2 plan and live repository truth as
  `d843b9a`; the QR Phase 1 files remain untouched.
- 2026-07-21: Hardened direct-script imports, public artifact detection, and
  adapter/reference tests as `8a8ad42`; Pre-CR and the focused suite remain green.
- 2026-07-21: Final static checks reached Ruff PASS, basedpyright zero errors
  with JSON-typing warnings, and Vulture PASS.
- 2026-07-21: Clean-room archive verification passed skill, catalog, safety,
  focused tests, dry-run, apply, and no-overwrite checks without external CLIs.
- 2026-07-21: Recorded the final verification evidence in `bc16385`.
- 2026-07-21: Fast-forward integrated the verified feature branch into `dev` at
  `c8fe9fe`; no release tag or publish was performed.
- 2026-07-21: Updated the live branch and release handoff state on `dev` in
  `ad84351`.
- 2026-07-21: Preserved the existing Research Domain Writing and Terrace skill
  locations and retained the existing skill validator.
- 2026-07-22: Added offline bootstrap classification to the environment-legibility
  audit and safe-tool-guards contract; catalog, public-safety, workbench, and
  focused tests pass in `1709a15`.
- 2026-07-22: Mined and sanitized nine durable first-party workflow patterns,
  added forward-test fixtures and the `0.3.0` manifest, and committed them as
  `1762727`; public validators, Pre-CR, and clean-room no-overwrite checks pass.
- 2026-07-22: Folded durable delegation, change-surface evidence, claim-to-
  evidence rules, and report-first instruction routing into existing public
  workflows as `f5389ac`; catalog, safety, workbench, unit, Ruff, and Vulture
  checks pass.

## Open Problems

- The current clean tree produces no coverage result when pre-CR is run without
  a changed diff; staged feature-branch commit gates already passed against
  non-empty diffs.
- Ruff, basedpyright, and Vulture are available for the dependency-free Python
  package; basedpyright reports only dynamic-JSON typing warnings.

## Quality Ladder Notes

- **Skill validation:** `python3 scripts/validate_skills.py` PASS.
- **Catalog validation:** `python3 scripts/validate_catalog.py` PASS.
- **Public safety:** PASS after the truth-surface update; excluded QR planning
  remains separate from the installable public asset set.
- **Focused tests:** `python3 -m unittest discover -s tests -p 'test_*.py'` PASS.
- **Pre-CR:** non-empty feature diff PASS with 67% aggregate changed-line
  coverage, threshold 0%, and anti-slop PASS.
- **Clean-room:** standard-library checkout passed validation and disposable
  target installation; a second apply was rejected without overwriting files.
- **Clean-tree Pre-CR:** expected `no-changes` baseline returns no coverage
  result; the staged non-empty feature diff passed the same gate during commit.

## Next Concrete Steps

1. Complete the final cross-repository status review for the additive v0.3.0 release.
2. Keep the AIOS generated library archival and its local runtime references intact.
3. Keep the QR-remediation phase on its separate execution track.

## QR Remediation Planning

- The existing QR-remediation phase remains a separate planning track and is
  not rewritten or folded into the Portable Agentic Workbench phase.
- New packaging planning lives in `.planning/phases/02-portable-agentic-workbench/`.
