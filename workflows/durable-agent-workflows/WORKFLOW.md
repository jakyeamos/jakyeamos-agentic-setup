# Durable Agent Workflows

Use this workflow when an agent task must survive interruption, delegation, or repeated execution without losing its contract or evidence.

## 1. Persist the contract

Create a durable workspace record with objective, owner, baseline, status, boundaries, and next step. Create a goal record with a stopping condition. Store each meaningful output as a named artifact with provenance, freshness, and a link from the goal.

## 2. Separate steering from execution

Keep human decisions, approvals, and scope changes in a steering record. Keep queue items independently runnable with inputs, dependencies, retry limits, and expected outputs. An agent may resume an approved queue item but may not reinterpret a steering decision silently.

## 3. Bound automation

Automation may collect evidence, run approved checks, and prepare drafts. It must stop for new credentials, external communication, destructive operations, unresolved ownership, or a material scope change. Every recurring action needs an idempotency rule, a failure state, and a human escalation path.

## 4. Preserve memory and handoff

Write concise state snapshots rather than unbounded transcripts. Link decisions to artifacts, distinguish observed facts from inference, and mark stale evidence. On interruption, leave a next action, blockers, and safe resume point. Completion means the verifier passed and the stopping condition is recorded.

See [the skill contract](../../skills/durable-agent-workflows/SKILL.md).
