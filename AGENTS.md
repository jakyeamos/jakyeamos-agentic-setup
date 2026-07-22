# Jakyeamos agentic setup

This is the public, vendor-neutral catalog and setup engine. Always-loaded
content is limited to hard stops and routing pointers; detailed payloads stay
in their owning skill, workflow, adapter, or project context directory.

## Invariants

- Read before modifying and preserve existing ownership and provenance.
- Do not publish or copy credentials, private paths, transcripts, caches,
  session state, or host-managed registration files.
- Use explicit manifest and target paths. Never overwrite an existing target or
  delete an unknown live member.
- Keep unresolved conflicts visible. `AUDIT_COMPLETE` is the stopping state;
  `MIGRATION_COMPLETE` requires an explicitly empty conflict ledger.

## Routing

- Manifest, schema, path, provenance, or drift questions: read
  [`docs/agent-config-manifest.md`](docs/agent-config-manifest.md).
- Decision-tree precedence or runtime mapping: read
  [`docs/agent-config-routing.md`](docs/agent-config-routing.md), then the
  narrow adapter under `adapters/<runtime>/`.
- Conflict, sync, or install behavior: read
  [`docs/agent-config-conflicts.md`](docs/agent-config-conflicts.md).
- Public mining or promotion: read [`docs/mining.md`](docs/mining.md) and load
  the `skill-harvest-and-promotion` skill/workflow on demand.
- Catalog asset work: start at [`catalog/manifest.json`](catalog/manifest.json)
  and load only the matching asset entrypoint.

The Python catalog surface remains available for catalog inspection. The
manifest-aware Node setup surface is routed through `agent-config`; see the
manifest contract for its command list and explicit dry-run/apply boundary.
