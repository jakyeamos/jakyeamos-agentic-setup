# Case study: environment legibility audit

## Problem

An agent can find a repository and still lack the small, current map needed to
work safely: architecture boundaries, verified commands, approval gates,
rollback behavior, and the minimum context to load. Documentation presence
alone does not establish that those surfaces are usable.

## Mechanism

The `environment-legibility-audit` workflow discovers repository identities,
separates checkout state from codebase identity, scores applicable controls,
and emits evidence-backed remediation plans. It uses disposable protected
baselines for dynamic checks and keeps public projections aggregate-only.

## Evidence

The workflow was derived from a cross-repository audit implementation that
records duplicate-origin grouping, linked worktree state, context freshness,
command verification, redaction, replay, and blocked-baseline outcomes. A
bounded dynamic pilot also showed that fresh disposable archives can trigger
package-manager or Python-runner bootstrap attempts; the prevention contract
now records those as blocked or unavailable instead of mislabeling them as
quality failures.

## Limitation

Static evidence and allowlisted command checks cannot prove that every agent
will select the best context or that deployment behavior is safe in every
environment. Human review remains required for remediation and publication.
