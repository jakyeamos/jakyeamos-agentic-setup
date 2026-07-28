# Execution Reassessment

Use this workflow when repeated failure, repeated manual setup, lifecycle
invalidation, or an unstable fallback shows that the current execution path is
creating churn.

## 1. Admit the trigger

Confirm the repeated symptom or lifecycle transition. A first-time failure
without invalidated state remains ordinary diagnosis and does not enter this
workflow.

## 2. Freeze repeated side effects

Stop the current remediation. Do not request the same approval, regenerate the
same artifact manually again, or repeat the same fallback while the cause is
being assessed.

## 3. Map the invalidated boundary

Inspect only the relevant boundaries: identity, signing or path stability,
lifecycle hooks, persistence, cache, dependencies, generated artifacts,
permissions, or fallback availability. Separate observed evidence from a
working hypothesis.

## 4. Select the smallest execution change

Prefer a change that removes recurring user work at its source: stabilize an
identity, make setup canonical, add a fail-fast diagnostic, repair lifecycle
ordering, or replace an unreliable fallback. Keep credentials, security
settings, destructive actions, external communication, and scope expansion
behind explicit approval.

## 5. Verify the transition

Run a narrow regression that includes the transition that caused the recurrence
(for example, a rebuild, reinstall, restart, or deployment). Record `passed`,
`blocked`, or `not run`; do not turn an unrun check into a success claim.

## 6. Resume or stop

Resume the original workflow only after the regression passes. Otherwise stop
with the compact five-field report from the skill and leave the next safe
action visible.

See [the skill contract](../../skills/execution-reassessment/SKILL.md).
