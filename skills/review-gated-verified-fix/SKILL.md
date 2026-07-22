---
name: review-gated-verified-fix
description: Use when an agent should turn an admitted repository issue into an isolated, evidence-backed fix that stops at human review instead of silently merging or publishing.
---

# Review-Gated Verified Fix

Use this skill for bounded implementation after a reproducible issue has been
admitted. It protects the baseline, isolates execution, verifies quality and
acceptance independently, and produces a review packet.

Do not use it to bypass review, operate on a dirty or unverifiable baseline,
perform outbound communication, or auto-merge a change.

## Contract

1. Require a reproducible issue, protected baseline, allowed paths, and risk
   assessment.
2. Create a disposable worktree or equivalent isolated checkout.
3. Run only the bounded provider command and explicitly allowlisted checks.
4. Reject changed paths outside the task scope.
5. Run quality gates and an independent acceptance check.
6. Record patch, commands, outcomes, limitations, rollback reference, and
   review decision in a packet.
7. Stop with `proposed`, `rejected`, `blocked`, or `accepted-for-review`; never
   claim completion from a clean process exit alone.

## Hard stops

Dirty or unverifiable baselines, missing gates, missing acceptance checks,
network or secret access outside policy, unexpected paths, timeouts, and any
request to merge or publish without explicit review.

See the [verified-fix workflow](../../workflows/review-gated-verified-fix/WORKFLOW.md).
