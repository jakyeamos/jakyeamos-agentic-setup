# Context Budget Governor

Use this workflow when a task has accumulated enough conversation, tool output,
or pasted source material that the next useful action may be obscured by the
context itself.

## Policy

The default hard checkpoint is 150,000 estimated tokens. Treat 135,000 as a
soft warning when the host can estimate usage. These are operating defaults,
not a claim that every model or host has the same context behavior. If the
host does not expose token counts, use observable pressure signals instead:
repeated re-reading, lost constraints, contradictory state, or an imminent
host compaction event.

When the hard checkpoint is reached:

1. Stop adding exploratory material.
2. Finish or safely pause the current tool call.
3. Write a checkpoint using `CHECKPOINT_TEMPLATE.md`.
4. Keep only the compact checkpoint, the active user objective, governing
   instructions, and the minimum evidence needed for the next action.
5. Resume from the checkpoint and verify that no acceptance condition was
   dropped.

The checkpoint is a handoff artifact, not a transcript. Do not copy raw
session logs, credentials, environment files, browser state, or private paths
into it.

When a checkpoint cannot establish a complete state, write a sanitized,
machine-readable boundary instead of filling the gap with a guess. The
checkpoint must retain the known objective and next action, set `status` to
`blocked` or `unknown`, and name the missing evidence. Never copy secrets,
raw logs, credentials, environment files, browser state, or host-private paths
into the checkpoint.

## Host adapter contract

The generic workflow does not register hooks. A host adapter may observe a
token estimate, stop-hook event, or compaction lifecycle event and stage a
checkpoint request. Registration must remain explicit and reviewable. The
adapter must fail closed when it cannot preserve the checkpoint or cannot
tell whether the threshold was reached.

## Checkpoint quality gate

Before resuming, confirm that the checkpoint names:

- the single current objective and its success condition;
- completed work and verified evidence;
- files or external state changed by the session;
- constraints, risks, and unresolved decisions;
- the next concrete action and the smallest verification that proves it.

The evidence section must distinguish observed facts from hypotheses. A
checkpoint that says “performance improved” without a measured comparison is
not evidence; record the observation and label the hypothesis instead.

See the [checkpoint template](CHECKPOINT_TEMPLATE.md) and the
[compaction case study](../../docs/case-studies/context-compaction.md).
