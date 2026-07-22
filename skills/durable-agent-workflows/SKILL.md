---
name: durable-agent-workflows
description: Use when work spans checkpoints, sessions, agents, or external state and needs a durable workspace, explicit goal, reviewable artifact, bounded automation, and honest stopping condition.
---

# Durable Agent Workflows

Use this skill when the conversation cannot safely remain the source of truth.
Create a durable workspace or artifact that preserves decisions, blockers,
owners, verification, known pitfalls, and the next action.

## Contract

Every durable goal declares an objective, verifier, stopping condition, allowed
surfaces, out-of-scope surfaces, current checkpoint, and next action.

Substantial work uses a reviewable artifact connecting expected behavior,
implementation state, test state, failures, fixes, and final verification.
Steering changes the current direction; queueing records later work without
silently interrupting the current checkpoint. Communication and destructive
automation remain approval-gated.

Do not create transcript dumps, duplicate summaries, speculative memory, or
automation that sends, deletes, deploys, or publishes without explicit scope.

See the [durable workflow](../../workflows/durable-agent-workflows/WORKFLOW.md).
