---
name: repo-behavior-spec-loop
description: Use for mature repositories that need a code-derived behavior inventory, canonical feature specification, running-app verification, defect remediation, regression coverage, and final evidence audit.
---

# Repository Behavior Specification Loop

Use this skill when a repository has enough surface area that a known-good
state requires exhaustive behavior evidence rather than a narrow QA pass.

Do not use it for prototypes, small bug fixes, generic test-strategy reviews,
or repositories that fail the maturity gate. Prefer a focused smoke loop when
the full inventory would cost more than it protects.

## Contract

1. Establish the maturity gate and choose a protected baseline.
2. Create exactly one canonical tabular behavior ledger.
3. Derive expected behavior from source and cite the responsible files or
   symbols without treating source presence as proof.
4. Test rows with the strongest available command, browser action, or manual
   method and record observed evidence.
5. Fix only logged defects with the smallest safe change.
6. Re-test, add regression coverage or a justified manual-only reason, and run
   a boundary audit.
7. Stop after repeated failed fix cycles and leave the row explicitly blocked.

## Verification rule

A row is verified only with source citation, test method, exact action,
observed result, evidence reference, iteration, baseline commit, and no open
functional, permission, security, data-integrity, or logistical defect.

See the [behavior loop](../../workflows/repo-behavior-spec-loop/WORKFLOW.md).
