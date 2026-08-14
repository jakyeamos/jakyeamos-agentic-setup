---
name: agentized-task-packet
description: Use when a human request needs to become an execution-ready agent packet with normalized intent, targeted context, constraints, verification, acceptance, and handoff requirements.
---

# Agentized Task Packet

Use this skill as a compiler from ambiguous human intent into an executable,
reviewable work contract. Preserve the user's objective while removing
guesswork about scope, evidence, and completion.

Do not use a template match as authority over the request, load every document
by default, or emit a prose-only plan when structured fields would prevent
ambiguity.

## Contract

Produce a packet containing:

- original request and normalized objective;
- task family, execution mode, assumptions, risks, and non-goals;
- targeted context sources and relevant skills;
- allowed surfaces and explicit boundaries;
- standards, verification commands, acceptance criteria, and stopping rules;
- deliverables, handoff format, optional project-note updates, and
  learning/writeback proposal when applicable.

Treat allowed paths as an exact inspection allowlist. Do not expand from named
files into sibling files, repository metadata, history, or configuration merely
because they might be useful; name the proposed expansion and request authority.

Build the verification plan before execution starts. Explain why any
sub-agent or model split adds value; otherwise keep the work single-threaded.

When the target itself is undefined, mark objective, context, boundaries,
roles, verification, acceptance, artifacts, and writeback as unknown or
blocked. Do not fabricate a generic plan, role assignment, or acceptance
criterion. Ask one minimal scope question that binds both target and working
surface, such as: “Which system or repository is in scope, and what surface
should be improved?”

See the [task-packet workflow](../../workflows/agentized-task-packet/WORKFLOW.md).
