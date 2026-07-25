# Canonical implementation examples

- `catalog/manifest.json` is the reference for asset IDs, provenance,
  supported targets, evidence, and manual-review installation metadata.
- `src/manifest.mjs` and `src/routing.mjs` show the boundary between manifest
  parsing, validation, and route-DAG behavior.
- `src/snapshots.mjs` and `src/agent-config.mjs` show deterministic snapshots,
  conflict detection, dry-run behavior, and refusal to overwrite live files.
- `workflows/safe-tool-guards/CONTRACT.md` is the reference for explicit
  targets, dry-run, approval, and blocked/unavailable outcomes.
- `workflows/environment-legibility-audit/WORKFLOW.md` is the reference for
  evidence, freshness, disposable baselines, replay, and removal conditions.

New assets should add a manifest entry, a local-link and public-safety check,
and a behavior fixture before they are described as portable or stable.
