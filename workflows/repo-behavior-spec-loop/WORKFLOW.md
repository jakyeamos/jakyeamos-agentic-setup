# Repository Behavior Specification Loop

Use this workflow when a mature repository needs its expected behavior made explicit, verified, and regression-safe.

## 1. Establish eligibility

Confirm that the repository has a runnable canonical path, a stable artifact or output that represents behavior, and a way to cite source evidence. If the target is too immature or has no observable contract, record a boundary report instead of inventing one.

## 2. Create one canonical ledger

Use one tabular behavior artifact per scope. Each row should include an identifier, source citation, exact action, expected result, observed result, evidence reference, status, owner, and last verification. Keep source citations close to the behavior they support.

Recommended statuses are `planned`, `covered`, `passed`, `failed`, `blocked`, `deferred`, and `not-applicable`. Do not use a blank or optimistic status to hide missing evidence.

## 3. Run the loop

Work through: plan, catalog, coverage, test, fix, re-test, regression, boundary, and report. Test the canonical user action, capture evidence, make the smallest durable fix, then repeat the targeted test and the relevant regression set.

Stop after three failed fix iterations for the same behavior unless a human explicitly changes the scope. Classify the remaining issue as blocked, deferred, or a complexity-boundary finding. A complicated workaround is not evidence of a passing contract.

## 4. Report completion

Completion requires the ledger, source citations, runnable verification command, evidence locations, unresolved boundaries, and a summary of regressions. A plan, help screen, test stub, or file presence alone is foundation-only and cannot close the loop.

Use the [structured behavior fixture](../../fixtures/behavior/behavior-spec-template.json) when a machine-readable starter contract is useful.

See [the skill contract](../../skills/repo-behavior-spec-loop/SKILL.md).
