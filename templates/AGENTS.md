# Low-loaded repository router

Always-loaded content is limited to invariants, hard stops, and pointers.
Load the matching route only when the task needs it.

## Invariants

- Preserve ownership, provenance, review gates, and higher-layer precedence.
- Close material consequences beyond the direct diff. Trace affected behavior,
  consumers, projections, maturity evidence, distribution, and machine-readable
  access; raise reusable candidates with their disposition and exact blocker.
- Never copy credentials, private paths, transcripts, caches, or host-managed state.
- Never overwrite an existing target or delete an unknown live member.
- Keep unresolved conflicts visible; `AUDIT_COMPLETE` precedes
  `MIGRATION_COMPLETE`.

## Routing

- Manifest, schema, provenance, or drift: read `docs/agent-config-manifest.md`.
- Route selection or runtime mapping: read `docs/agent-config-routing.md` and
  the narrow adapter for the active runtime.
- Conflict or sync decision: read `docs/agent-config-conflicts.md`.
- A material cross-surface implementation consequence: load the
  `consequence-closure` skill.
- A matching skill, agent, command, or workflow: load only that on-demand
  payload after the route resolves.
- Public mining or promotion: read `docs/mining.md` and the
  `skill-harvest-and-promotion` workflow.
