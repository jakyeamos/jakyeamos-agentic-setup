# Governed work loop

Use the same five states for a small fix, a repository audit, or a multi-step
agentic workflow:

```text
route -> context -> execute -> verify -> handoff
```

## Route

Name the user outcome, repository boundary, risk level, and the appropriate
workflow or skill. If the request is strategy-only, keep the lane conceptual.

## Context

Load governing instructions, current truth, and only the references needed to
act. Record assumptions and identify any external dependency before mutation.

## Execute

Make the smallest coherent change. Use explicit target roots, dry-run capable
commands, and existing repository behavior. Keep vendor adapters separate from
the portable contract.

For work that spans checkpoints, agents, or external state, persist the goal,
artifact, and next action using the [durable workflow contract](../../skills/durable-agent-workflows/SKILL.md).
For ambiguous delegated work, compile an [agentized task packet](../../skills/agentized-task-packet/SKILL.md)
before execution. Keep steering and approval separate from queue items, and do
not treat a handoff as acceptance.

## Verify

Verify the behavior, not only the file presence. Run focused tests first, then
the repository quality ladder. Capture command, result, and limitation. A
failed quality tool is evidence to surface, not a success to reinterpret.

## Handoff

Update the live truth snapshot and leave a compact next action. Include the
branch, changed surface, verification evidence, open risks, and whether any
publish or registration step remains manual.

This loop is intentionally a workflow contract, not an agent runtime. See the
[governed execution case study](../../docs/case-studies/governed-execution.md).
