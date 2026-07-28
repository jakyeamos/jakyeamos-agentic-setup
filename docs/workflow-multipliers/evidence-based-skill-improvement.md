# Evidence-based skill improvement

Evidence-based skill improvement treats an agent skill as a hypothesis about
agent behavior, not as finished prose that becomes trustworthy when published.
The goal is to improve the behavior the skill produces and preserve the
evidence that justifies each revision.

This is a reusable method, not a prescribed evaluation stack. It can be used
with a local harness, a test repository, TMCP, an evaluation runtime, or a
small set of carefully chosen manual trials.

It is intentionally a reference rather than an agent-invoked skill in this
catalog. The method is useful now, but its own routing and output behavior
should earn a broader clean-room corpus before it is promoted into a runtime
trigger.

## The multiplier

Out-of-the-box agent setups usually add instructions and assume they help.
This method creates a feedback loop around those instructions:

```text
observe -> specify -> test -> compare -> revise -> regression-test -> promote
```

It makes skill quality a behavioral question:

- Does the skill trigger for the work it is meant to cover?
- Does it stay out of unrelated work?
- Does it produce the promised artifact or decision?
- Does it preserve the intended safety boundary?
- Does the revised version behave better than the prior version or control?

## When to use it

Use this method when a skill is repeatedly used, being prepared for public
sharing, or producing ambiguous results. It is especially useful when static
review identifies broad triggers, missing output contracts, buried required
reads, or unclear stopping conditions.

Do not use a static warning as a conclusion. A warning identifies an
investigation target; it does not establish that the skill is ineffective.

## Improvement loop

1. **State the current contract.** Record the intended trigger, non-trigger,
   inputs, outputs, safety boundary, verifier, and stopping condition.
2. **Build a small test set.** Include representative positive cases,
   representative negative cases, and at least one known failure or edge case.
3. **Establish a control.** Compare the current skill with the previous skill,
   an unassisted run, or another explicitly named candidate. Keep the control
   stable for the comparison.
4. **Run the behavior.** Capture routing, actions, artifacts, verification,
   refusal or stop behavior, and unresolved uncertainty.
5. **Diagnose the mismatch.** Separate trigger failure, instruction failure,
   tool failure, environment failure, and judging failure.
6. **Revise the smallest useful surface.** Change the skill, workflow, test
   case, or contract that explains the observed mismatch.
7. **Run regression cases.** Re-test the changed behavior and the cases that
   previously passed. A local improvement that breaks a safety or
   non-trigger boundary is not an improvement.
8. **Record the disposition.** Promote, strengthen, defer, or reject the
   candidate with the evidence and remaining gaps attached.

## Minimum viable experiment

Before changing a skill, write a small experiment record. It can be a Markdown
note or a structured fixture, but it should answer the same questions:

```text
candidate: <skill or workflow identity and revision>
task_set: <bounded positive, negative, and edge cases>
control: <previous revision, unassisted run, or named alternative>
trigger_rule: <what should activate and what should stay out>
output_contract: <artifact, decision, or refusal that must appear>
safety_boundary: <side effects, approvals, and stop conditions>
observed:
  - <case, result, artifact, and unresolved uncertainty>
diagnosis: <trigger | instruction | tool | environment | judge>
change: <smallest surface changed and why>
regression: <prior passes and safety/non-trigger cases re-run>
disposition: <promote | strengthen | defer | reject>
next_stop: <what evidence is still required>
```

Do not fill an unknown field with an optimistic default. A missing runner,
unclear control, unavailable dependency, or unreviewed side effect belongs in
the record as `unknown`, `blocked`, or `manual-review`.

## Separate the judgments

A useful trial keeps at least three questions distinct:

| Judgment | Question | Failure diagnosis |
| --- | --- | --- |
| Routing | Did the candidate activate for the intended task and stay out of the non-trigger? | Trigger or precedence defect |
| Behavior | Did it produce the promised artifact, decision, or stop state? | Instruction or tool defect |
| Boundary | Did it preserve scope, uncertainty, approval, and human acceptance? | Safety or environment defect |

The same run may pass one judgment and fail another. Do not collapse a routing
pass into a usefulness claim, or a useful artifact into authorization to apply
it.

## Promotion rule

Promotion is justified only when the candidate has a named contract, a
representative positive and negative set, a control, observable outputs, and a
regression result that preserves its safety boundary. If any of those are
missing, keep the candidate as a reference or mark it `strengthen` rather than
calling it stable.

The promotion rule is deliberately portable. A TMCP campaign, an evaluation
runtime, a repository fixture, or a human-run trial can supply the evidence;
the tool is not the evidence.

## Evidence levels

Evidence should be labeled rather than collapsed into one confidence claim:

| Level | What it establishes | What it does not establish |
| --- | --- | --- |
| Static inspection | A contract or wording risk is visible | That the agent will fail in practice |
| Trigger tests | Routing behavior on selected positive and negative cases | General usefulness across tasks |
| Output checks | Whether promised artifacts or fields appear | Whether those artifacts improve outcomes |
| Paired comparison | A difference between a candidate and a named control | A durable effect across a broad corpus |
| Repeated task-set evaluation | Stability across representative work | Universal improvement for every user or setup |

Do not claim model-quality or developer-speed improvement from prose quality,
static lint, one successful run, or identical candidate hashes alone.

## Portable output

An adopter can apply the method without adopting this repository's tools. A
useful improvement record contains:

- the skill version or candidate identity
- the task set and control definition
- positive and negative trigger cases
- observed behavior and produced artifacts
- the judge or acceptance rule
- the change made and why
- regression results
- unresolved evidence gaps and the next stopping condition

The record may be a Markdown note, test fixture, structured evaluation
report, or another local artifact. The format is secondary to traceability.

## Relationship to other multipliers

This method can stand alone or pair with:

- [`skill-harvest-and-promotion`](../../skills/skill-harvest-and-promotion/SKILL.md)
  to decide whether a private practice is ready for public reuse.
- [`repo-behavior-spec-loop`](../../skills/repo-behavior-spec-loop/SKILL.md)
  to derive expected behavior and regression evidence from a repository.
- [`evaluation-evidence`](../../workflows/evaluation-evidence/WORKFLOW.md)
  to keep observations, hypotheses, limitations, and claims distinct.
- external evaluation or orchestration tools, when their runtime and data
  boundaries are appropriate for the adopter's setup.

These are optional relationships, not dependencies or a required sequence.

The [documentation-as-principles](documentation-as-principles.md) reference
is useful when the experiment record needs a durable home, a freshness rule,
and pointer-only summaries across several instruction surfaces.

## Promotion boundary

This reference should become an agent-invoked skill only after the improvement
loop itself has been forward-tested across clean-room examples. Until then,
the portable contribution is the method and evidence contract, not a claim
that the method automatically improves every skill.
