# Evidence-backed design assessment

Use this route for a bounded request to challenge an implementation, simplify a
subsystem, or reassess after a capability change. Ordinary edits still use the
small change-context packet; do not require this review for every task.

## Purpose before mechanism

Read the affected accepted outcomes, constraints, handoffs, active commitments,
and canonical behavior specifications. Ask what outcome each mechanism serves.
Do not infer purpose from code or treat an architecture decision as permanent.
An accepted constraint remains authoritative until explicitly reconciled even
when its rationale is challenged. Proposed or inferred rationale stays proposed.

A consequential decision may add `reasoning` with schema
`compass-decision-reasoning/v1`, `kind` (`outcome`, `constraint`, or
`implementation`), and `assumptions`. Each assumption has a stable `id`,
`statement`, `status` (`supported`, `challenged`, or `unknown`), `evidence_refs`,
and `reconsider_when`. Missing reasoning on older decisions means unknown;
never infer a classification. Empty evidence is allowed for unknown/challenged
assumptions, never for supported ones. Reference existence is not confirmation
that an assumption is true. Relevant assumption evidence participates in proof
freshness. Do not add records for every function.

## Compare before recommending

Submit `compass-modernization-proposal/v2` through the existing `assess` command.
Keep original fields: explicit paths/compass_ids, base_revision, problem,
expected_benefit, applicable, applicability_reason, evidence_refs, rollback,
and existing remediation_id for changes. A retention decision needs no ticket.
Add:

- `alternatives`: 3–12 alternatives covering `delete`, `simplify`, and `retain`;
  optional `optimize` and `automate`. Each has unique `id`, `kind`, `summary`,
  `consequences`, `consumer_impact`, `tradeoffs`, affected `outcome_ids`, and
  `evidence_refs`. Explain what would break, including operational, privacy,
  compatibility, failure-recovery and external consumers where relevant. A
  ruled-out alternative still deserves an evidence-backed reason.
- `selected_alternative`: an alternative ID; selection is a proposal.
- `reconsider_when`: the evidence or condition that would reopen the decision.
- `benefit_check`: nonempty unique `measures`, `baseline_ref`, `method`, and
  `success_condition`. Measures may be qualitative; fewer lines alone do not
  demonstrate lower total maintenance burden. For retention, measure whether
  the current design continues meeting its outcome and constraints.

Prefer deletion only when obligations survive. Then consider simplification,
optimization and automation, accounting for migration cost and ongoing burden.
Do not invent a problem to justify a model release or a desired refactor.

## Proposal completeness is not justification

The initial assessment returns `proposal_complete`, `review_target`, and
`evidence` references with digests. Missing review remains insufficient evidence.
Read the actual code, specifications and evidence before writing a review. Do
not generate five supported findings by copying the proposal's claims. An
existing file, passing smoke test, or confident author is not semantic evidence.

Record the review in a separate local document, then supply a `review` object:

- `schema`: `compass-assessment-review/v1`;
- `subject_digest`: the reviewed `review_target`;
- `reviewer`: actual human or agent identity, never impersonated;
- `source_ref` and `source_digest`: local review document and current digest;
- `verdict`: `justified`, `retain`, `rejected`, or `insufficient`;
- `rationale`: concrete reasoning for the selected disposition;
- `claims`: exactly `problem`, `causal_fit`, `benefit`, `alternatives`, and
  `preservation`. Each has `finding` (`supported`, `contradicted`, `unknown`),
  `rationale`, and `evidence`: objects containing `ref` and current `digest`.
  Findings evaluate the selected alternative; retaining protective complexity
  can be supported even though the proposed deletion was disproved.

Run assess again. Current review with supported claims can return worthwhile_now
or alongside_planned_work; a consistent retain verdict returns
retain_current_design. Rejection returns rejected. Missing, stale, contradictory,
or insufficient review cannot become a positive recommendation. The helper
checks structure and source freshness; it does not authenticate the reviewer or
understand prose. Recorded review is not owner approval, execution authority,
or a substitute for independent Quality Runner and preservation proof.

Use a separate reviewer for consequential or disputed recommendations. If
independent review is unavailable, say so; never label self-review independent.
After any affected source, proposal or evidence changes, revisit the reasoning
before recording a fresh digest. Do not mechanically refresh hashes to make a
stale recommendation green. Every disposition creates zero implementation work.
Legacy v1 proposals remain readable but cannot silently become reviewed advice.
The output retains `compass-modernization-assessment/v1` for existing consumers,
with additive `review_contract`; consumers must preserve unknown dispositions.

## Check whether the benefit happened

Save the pre-change reviewed assessment as local evidence. After separately
authorized work, keep the original base and add `observation` to the proposal:

- schema `compass-benefit-observation/v1`;
- `assessment_ref` and `assessment_digest` identify that exact saved assessment;
- `result`: realized, not_realized, mixed, or unknown;
- `comparisons`: exactly one per promised measure, with `measure`, textual
  `before`, `after`, `interpretation`, and local `evidence_refs`.

Assess returns a separate benefit_observation.review_target. Review the actual
measurements and supply an observation `review` using the same review format,
but claims `attribution`, `measurement`, `preservation`. A justified, supported,
current review is required to expose the declared result as reviewed. It remains
unknown otherwise. Test whether workload differences or shifted complexity
explain apparent improvement. Do not substitute passing preservation tests for
benefit evidence, or benefit evidence for the completion gate. A failed benefit
claim is a result to retain, not a reason to fabricate success or automatically
roll back. Historical recommendation review can become stale after the change;
the separate source-bound observation is how the result is assessed.

## Reference patterns and dogfood bar

This adapts explicit assumptions and alternatives from
[MADR](https://adr.github.io/madr/decisions/0000-use-markdown-architectural-decision-records.html)
and applicability separate from execution from
[OpenRewrite](https://docs.openrewrite.org/reference/yaml-format-reference).
No platform dependency or source implementation is copied.

Fresh-context trials must examine removable complexity, awkward-looking code
that protects a constraint, and a sound subsystem that should remain unchanged.
Grade grounded judgment and preserved intent, not a preferred refactoring style.
A model release alone, unverified evidence, or unsupported benefit must not
produce a recommendation to change code. Run negative freshness and contradictory
review cases through the public helper as well as unit tests.

Planned-work references are required to resolve locally and are included in the
review digest. Editing or deleting the plan invalidates its recommendation.
Unrelated commits do not invalidate a review when its explicit base and relevant
inputs remain unchanged. Proposal input is limited to 1 MiB.
