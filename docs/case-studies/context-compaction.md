# Case study: context compaction

## Problem

Long agent sessions accumulate instructions, tool output, stale hypotheses, and
repeated source material. The next action becomes harder to identify even
when the relevant facts are still present somewhere in the session.

## Mechanism

`context-budget-governor` defines a soft warning at 135,000 estimated tokens and
a hard checkpoint at 150,000. It stops exploration, writes a compact checkpoint,
and resumes only after the acceptance conditions and evidence are restated.
The policy is vendor-neutral; the host adapter decides how token pressure or a
compaction lifecycle event is observed.

## Evidence

The source audit observed a 150,000-token compaction boundary and lifecycle
hooks in an existing agent host. The repository now has a deterministic
checkpoint template, a dry-run-safe installer, and tests that verify the
installer does not mutate a target during preview.

These are observations about configuration shape and package behavior. They
are not a measured comparison of model quality before and after compaction.

## Limitation

Token estimates vary by host and model, and this repository does not measure
answer quality, retrieval accuracy, or latency. The 150,000-token value is an
explicit operating default that should be calibrated with task-specific
evaluation evidence.
