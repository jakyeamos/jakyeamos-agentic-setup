# Consequence Closure

Use this workflow after live implementation evidence exposes a material
cross-surface consequence. For pre-edit advisory discovery, use the separate
evidence-backed change-surface mapper.

## 1. Establish the direct change and evidence boundary

Record the requested behavior, canonical owner, revision or snapshot boundary,
intended audience, current authority, and verification standard. Keep observed,
inferred, stale, blocked, and unknown evidence distinct.

## 2. Build the impact matrix

Derive surfaces from live contracts rather than a universal checklist. Inspect
the relevant consumers, schemas, generated artifacts, provider projections,
distribution manifests, telemetry, documentation contracts, rollout and
rollback surfaces, and machine-readable evidence seams.

For every material finding retain:

| Field | Required meaning |
| --- | --- |
| Owner | Repository, skill, service, or artifact that owns the truth |
| Relationship | Why the requested change affects this surface |
| Condition | Predicate controlling applicability |
| Evidence | Source, freshness, provenance, and uncertainty |
| Action | Required correction or recurrence reduction |
| Verification | Observable proof for the action |
| Disposition | `required`, `conditional`, `leverage`, `optional`, or `blocked` |

Follow supported causal edges as far as necessary. Stop when the next edge is
merely adjacent, speculative, or unrelated.

## 3. Resolve conditions without convenient defaults

Convert a true condition to required work. Record a false condition as not
applicable. Treat an unknown condition as a blocker to the affected maturity
claim or as reduced confidence.

Evaluate hosting, public distribution, provider projection, behavioral parity,
intended audience, and real-use availability independently. A UI badge, file
hash, copied source, or passing structural test proves only its own observation.

## 4. Close required and leverage findings

Implement each required impact and high-leverage recurrence reduction when the
owner is known and the current request already authorizes the work. Re-read
downstream repository guidance and ownership before crossing repository
boundaries.

If a relevant fact is available only in a UI, inspect the complete owning
feature and expose its machine-useful snapshot through a focused read-only CLI
or API. Derive UI and machine projections from the same persisted source and
preserve schema version, freshness, provenance, uncertainty, and blocked or
unknown states. Add parity tests against that shared source.

Do not turn this rule into a whole-product parity audit. Stop at the owning
feature unless another causal dependency is demonstrated.

## 5. Raise reusable candidates and exact blockers

For new or changed agent rules, skills, workflows, evaluators, and evidence
contracts, choose one promotion disposition:

- `strengthen` an existing asset when its trigger and authority stay aligned;
- create a `companion` when the behavior has a distinct trigger, output, or
  safety boundary;
- keep a `reference` when copying would duplicate another owner;
- `defer` a viable candidate until named packaging, evidence, ownership, or
  authority is available;
- `exclude` non-reusable, private, or unsafe behavior with the concrete reason.

Raise every strengthen, companion, and defer candidate in the next progress
update or handoff. Name the proposed owning asset or repository, reusable
advantage, supporting evidence, and exact blocker or next promotion gate.
Candidate detection alone does not authorize downstream mutation or
publication.

## 6. Verify and hand off

Verify the direct behavior, each applicable downstream correction, the complete
evidence projection, and the reassessed maturity claim. Return an impact receipt:

- affected owners and causal relationships;
- conditions evaluated as true, false, or unknown;
- cross-repository or distribution changes;
- verification and machine-readable evidence added;
- candidate dispositions and promotion gates;
- unresolved blockers and the exact action required to clear each.

Do not call the work complete while a required or leverage finding remains
unresolved. Keep publication, deployment, credentials, security changes,
destructive actions, and other external effects behind their existing approval
boundaries.

See the [skill contract](../../skills/consequence-closure/SKILL.md).
