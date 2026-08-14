---
name: execution-reassessment
description: Use when the same failure or manual setup repeats, a lifecycle transition invalidates trusted state, a one-time success does not survive its normal lifecycle, or a fallback is becoming recurring user work.
---

# Execution Reassessment

Use this skill as a gate against mechanically repeating an execution path that
keeps producing the same symptom. Optimize for the user's durable outcome,
not for completing the current procedure at any cost.

## Trigger

Reassess before repeating a remediation when one or more of these is true:

- The same failure or manual setup step has happened twice.
- A rebuild, restart, reinstall, deployment, or similar lifecycle transition
  invalidated permissions, approvals, identities, caches, generated artifacts,
  or other trusted state.
- A workflow succeeds once but fails after its normal lifecycle transition.
- A semantic or primary path is unavailable and the same coordinate, visual, or
  other fallback is being repeated.
- The proposed fix adds recurring user-only work to ordinary development.

## Do not trigger

Do not use this skill for a first-time failure with no invalidated state, an
ordinary diagnosis that has not repeated, or a one-off implementation defect
that does not require changing the execution path.

## Reassessment contract

1. **Stop the churn.** Do not repeat the current remediation, re-request the
   same approval, or ask the user to perform the same setup while reassessment
   is open.
2. **Capture the symptom.** Record what repeated, what preceded it, and which
   state was lost or invalidated.
3. **Inspect the boundary.** Check the relevant identity, lifecycle,
   persistence, cache, dependency, permission, generated-artifact, and
   fallback boundaries before changing user state again.
4. **Classify the cause.** Use an evidence-backed category such as
   implementation defect, environment prerequisite, lifecycle defect, unstable
   identity, stale state, or external blocker. Mark hypotheses and missing
   evidence instead of presenting them as facts.
5. **Choose the smallest change.** Change the execution mechanism, ordering,
   diagnostics, fallback, or narrowly scoped test that removes the recurring
   work. The change must name a concrete corrective execution adjustment, not
   only an inspection plan. If the boundary is still uncertain, choose the
   narrowest reversible diagnostic or stabilization change that will make it
   observable, and keep the uncertainty in `cause`. Do not expand the task
   merely because reassessment found a nearby improvement.
6. **Preserve safety boundaries.** Stop for new credentials, persistent
   access, security-sensitive settings, destructive actions, external
   communication, or a material scope change.
7. **Verify the lifecycle.** Run the narrowest regression that exercises the
   invalidating transition. Resume the original workflow only after the
   regression passes; otherwise report the blocker honestly.

## Output contract

Before resuming the original workflow, return exactly this compact structure:

```text
symptom: <what repeated or became invalid>
cause: <evidence-backed systemic explanation, with uncertainty marked>
change: <concrete corrective execution adjustment, not inspection alone, and why it removes the recurring work>
impact: <user action required now; explicitly name what must not be repeated while reassessment is open>
verification: <passed, blocked, or not run; narrow regression and result>
```

The `impact` field must make the immediate stop boundary explicit. The
`verification` field must not claim success from a plan, a clean process exit,
or an unrun check.
It must record the observed state transition when that is the regression—for
example, generated types appearing and the subsequent build completing cleanly.

## Stopping condition

Stop with the five-field report when the evidence is insufficient, the narrow
regression is blocked, or the next step would cross an approval or scope
boundary. A blocked reassessment is useful state; repeating the rejected path
is not.
