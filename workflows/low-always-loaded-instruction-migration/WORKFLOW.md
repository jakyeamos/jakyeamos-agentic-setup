# Low-Always-Loaded Instruction Migration

Use this workflow to move durable instructions out of a crowded startup surface while preserving behavior and making conflicts visible.

## 1. Inventory the startup surface

Collect only the instruction files and generated adapters that are actually loaded by the target runtime. Record, for each source:

| Field | Meaning |
| --- | --- |
| `source_id` | Stable logical identifier |
| `layer` | System, user, repository, module, or tool layer |
| `load_order` | Relative precedence or startup order |
| `owner` | Team or repository owner, not a credential or machine path |
| `status` | Active, duplicate, conflicting, stale, or unknown |
| `replacement` | Canonical portable skill or explicit `none` |

Do not infer that a file is loaded because it exists. Capture the loader, configuration, or runtime evidence that makes the source active.

## 2. Classify before changing

Compare instruction atoms, not whole files. Mark each atom as `compatible`, `duplicate`, `conflict`, `unknown`, or `host-specific`. A conflict must name both sources, the competing behavior, and the proposed precedence. Unknown or host-specific material remains in the report until an owner resolves it.

## 3. Separate report-only and apply modes

`audit` inventories the surface and writes a report. `drift` compares the current surface with the manifest. `doctor` checks expected files, links, and precedence. `sync` proposes a portable layout. `install` applies a reviewed plan only after an explicit apply decision.

Every report must end with `AUDIT_COMPLETE` and include counts for unchanged, movable, conflicting, unknown, and blocked items. A successful applied migration must end with `MIGRATION_COMPLETE`, the exact files changed, and a no-overwrite result.

## 4. Apply with hard stops

Never overwrite an existing instruction source, delete an unresolved conflict, or silently lower a higher-precedence rule. Refuse to apply when the manifest is incomplete, the source owner is unknown, the destination is occupied, or the plan changes protected runtime behavior. Produce a review packet for those cases instead.

## 5. Verify

Re-run the loader or equivalent startup check, then run `drift` and `doctor`. The migration is complete only when the expected portable skill is discoverable, the original source is either intentionally retained or explicitly retired, and the final report explains every exception.

See [the skill contract](../../skills/low-always-loaded-instruction-migration/SKILL.md).
