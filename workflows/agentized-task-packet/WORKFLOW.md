# Agentized Task Packet

Use this workflow to compile an ambiguous request into a bounded packet that another agent or operator can execute and verify.

## 1. State the objective

Write one outcome-oriented objective, then classify the work as investigation, implementation, review, migration, release preparation, or another named task family. List explicit non-goals so routine helpers do not expand scope.

## 2. Assemble targeted context

Include only the repository state, relevant files, prior evidence, constraints, and known unknowns needed for the task. Record the baseline, ownership status, dependencies, and the source of important claims. Do not attach every document or assume that a prompt is a substitute for repository truth.

## 3. Define execution and verification

Specify standards, allowed tools and paths, risk controls, time or iteration budgets, and the exact verification commands or observations. State what counts as acceptance and what evidence must be handed off. Choose subagents or models by task family only when the split improves coverage or independence.

## 4. Produce a handoff

The packet should contain: objective, classification, context, boundaries, standards, risks, plan, roles, verification, acceptance, artifacts, unresolved questions, and writeback location. A receiving agent must be able to report `complete`, `blocked`, or `needs-review` without inventing a new scope.

See [the skill contract](../../skills/agentized-task-packet/SKILL.md).
