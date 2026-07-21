# Case study: governed execution and evidence

## Problem

An agent can route to a plausible workflow and still leave an unverifiable
result, a hidden partial failure, or a handoff that drops the original
constraint.

## Mechanism

`governed-work-loop` makes route -> context -> execute -> verify -> handoff an
explicit state machine. `evaluation-evidence` adds a contract-shaped fixture
and requires each report to separate observed evidence, hypotheses, and
limitations. Richer evaluation contracts remain external references.

## Evidence

The audit found this loop documented in an existing local operating-system
design and found public contract projects that are better kept as dependencies
than copied into a skill package. The workbench preserves the boundary and
verifies its own catalog and installer behavior in a clean-room-friendly test
suite.

## Limitation

The workflow records whether checks ran; it does not make a weak check strong.
Evaluation quality depends on the fixture, baseline, and acceptance condition
chosen for the actual task.
