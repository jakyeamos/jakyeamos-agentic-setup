---
name: consequence-closure
description: Use when implementation evidence reveals material consequences beyond the requested diff, including affected consumers, projections, distributions, conditional maturity claims, UI-only agent evidence, or a reusable workflow advantage that must be raised with an exact promotion blocker.
---

# Consequence Closure

Close the material consequences of a change, not only its direct edit. Follow
demonstrated causal relationships across repositories and skills without a
fixed hop count, while stopping before unrelated improvement.

## Contract

1. Build a change-specific impact matrix from live repository contracts,
   canonical sources, consumers, projections, generated surfaces, distribution
   metadata, and verification evidence.
2. Record each material finding with its owner, causal relationship, condition,
   evidence and freshness, required action, verification, and disposition:
   `required`, `conditional`, `leverage`, `optional`, or `blocked`.
3. Treat every failure surfaced by a required validation gate as completion
   evidence until dispositioned. `Pre-existing` and `unrelated` describe
   provenance, not a reason to stop. Fix the failure in the same turn when the
   expected behavior is clear, the correction is local and reversible,
   verification is bounded, and no ownership or safety boundary is crossed.
   Otherwise preserve the affected work, name the exact blocker, and keep
   completion partial when the gate is required.
4. Resolve required impacts and high-leverage recurrence reductions when
   ownership and existing authority permit. Do not treat candidate detection as
   permission to mutate another owner or publish an artifact.
5. Preserve conditional truth:
   - `true` makes the finding required;
   - `false` makes it not applicable without reducing maturity;
   - `unknown` blocks the affected claim or lowers confidence.
6. Evaluate hosting, public distribution, provider projection, behavioral
   parity, intended audience, and real-use availability separately. Source
   identity and structural presence do not prove behavioral parity.
7. If a relevant governance or verification fact exists only in a UI, inspect
   the whole owning feature for machine-useful evidence and add read-only,
   backward-compatible CLI or API parity from the same persisted source. Keep
   the expansion feature-bounded.
8. Check whether the change creates a reusable advantage. Give it one
   disposition: `strengthen`, `companion`, `reference`, `defer`, or `exclude`.
   Raise every `strengthen`, `companion`, and `defer` candidate to the user with
   the proposed owner, advantage, evidence, and exact blocker or promotion gate.

Do not weaken ownership, credential, security, destructive-action, deployment,
publication, or external-effect boundaries to close an impact.

## Completion

Return a concise impact receipt covering affected owners, evaluated conditions,
cross-repository changes, evidence added, promotion candidates, and unresolved
blockers with the action that clears each one. Completion remains partial or
blocked while a required or leverage finding, including a required validation
failure, is unresolved.

Use the
[consequence-closure workflow](../../workflows/consequence-closure/WORKFLOW.md)
for the detailed execution sequence.
