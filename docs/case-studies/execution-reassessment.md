# Case study: execution reassessment

## Problem

An agent can keep asking for the same approval or repeating the same setup
because the visible symptom looks like a local failure. The durable cause may
be an identity, lifecycle, persistence, generated-artifact, or fallback defect.

## Mechanism

`execution-reassessment` freezes repeated side effects, inspects the boundary
that invalidated trusted state, classifies the systemic cause, chooses the
smallest execution change, and verifies the lifecycle transition before
resuming.

## Evidence

The source behavior supplied explicit triggers, safety boundaries, and a
five-field output contract. A blind clean-room evaluation initially passed two
of three trigger runs and the non-trigger run. The judge identified one
specific gap: a repeated artifact-setup case did not explicitly say to stop
the manual step. The public contract was tightened so `impact` must name what
must not be repeated and `verification` must state `passed`, `blocked`, or
`not run`.

The revised contract was then re-evaluated across the same cases: three of
three trigger runs passed and the non-trigger run passed. A separate judge
cleared the candidate for promotion while keeping the lifecycle regression
unverified in each artifact.

## Limitation

The skill changes the execution decision; it does not diagnose every root
cause or apply security-sensitive changes automatically. Its usefulness still
depends on boundary evidence and a narrow regression that exercises the actual
lifecycle transition.
