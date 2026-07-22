---
name: low-always-loaded-instruction-migration
description: Use when consolidating or migrating always-loaded agent instructions across runtimes, repositories, or editor surfaces while preserving precedence, ownership, conflicts, and safe installation behavior.
---

# Low Always-Loaded Instruction Migration

Use this skill to make startup instruction surfaces small, explicit, and
portable. Keep hard invariants and routing pointers always loaded; move detailed
policies, project context, skills, agents, commands, and workflows behind
discoverable routes.

Do not use it for ordinary documentation edits, a single-runtime wording
change, or a conflict that has not been approved for resolution.

## Contract

1. Inventory every live instruction surface and its owner.
2. Represent source, destination, runtime, layer, sync direction, provenance,
   and status in a manifest.
3. Separate invariant, routing, adapter, project-context, and on-demand layers.
4. Record contradictory or behavior-bearing content in a conflict ledger.
5. Run report-only audit, drift, doctor, and install checks before any apply.
6. Apply only to explicit targets, never by broad recursive copying.
7. Re-run validation and leave a compact migration receipt.

## Hard stops

- unknown ownership, broken links, missing targets, unresolved conflicts, or
  unsupported runtimes;
- overwriting existing user-owned instructions;
- credentials, host-managed state, raw transcripts, or machine-specific paths;
- declaring migration complete while the conflict ledger is unresolved.

## Output

Return the manifest path, source inventory, skipped sources, conflict ledger,
drift state, apply plan, verification results, and the exact remaining manual
step. Use `AUDIT_COMPLETE` before `MIGRATION_COMPLETE`.

See the [migration workflow](../../workflows/low-always-loaded-instruction-migration/WORKFLOW.md).
