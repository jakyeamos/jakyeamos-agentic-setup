# Review-Gated Verified Fix

Use this workflow for bounded issue remediation where correctness must be demonstrated before a human decides whether the patch is accepted.

## 1. Admit the issue

Normalize the issue into an objective, expected behavior, reproduction or evidence, allowed paths, excluded paths, risk level, and acceptance criteria. Reject vague work that cannot be verified or that expands into unrelated cleanup.

## 2. Protect the baseline

Record the starting revision and working-tree state. Execute changes in a disposable work area or equivalent isolated checkout. Never treat a dirty or unknown baseline as a clean comparison. Preserve user work and stop if ownership or scope is ambiguous.

## 3. Execute boundedly

Allow only the declared paths and commands. Set a time, output, and iteration budget. Run the smallest reproduction first, then the fix, then the targeted acceptance command. Do not auto-merge, publish, delete, or broaden the work when a gate fails.

## 4. Verify independently

Run the acceptance command from the protected baseline context, then the relevant regression gates. Capture exact commands, exit status, revision, changed paths, and artifacts. A green unit test is not enough when the user-visible behavior requires a runtime, browser, device, or integration check.

## 5. Handoff for review

Produce a review packet with the issue, evidence before the fix, patch summary, evidence after the fix, regressions, limitations, and a recommended disposition. Outcomes are `verified-ready`, `needs-review`, `blocked`, `rejected`, or `not-run`. Human acceptance remains a separate state.

Use the [verified-fix contract fixture](../../fixtures/review/verified-fix-contract.json) to validate packet shape.

See [the skill contract](../../skills/review-gated-verified-fix/SKILL.md).
