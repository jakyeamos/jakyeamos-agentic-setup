# Coding and catalog conventions

- Use Node ESM with explicit imports and standard-library APIs in the runtime.
- Use Python 3 with annotations and deterministic, sorted validator output.
- Treat `catalog/manifest.json` as the machine-readable asset source of truth;
  keep `catalog/index.md` and README examples aligned with it.
- Preserve stable asset IDs, schema versions, provenance classes, supported
  targets, and install modes. Changes to those fields require fixture coverage.
- Keep always-loaded files limited to invariants and routing pointers. Put
  procedures, examples, and host-specific details in routed packets.
- Preserve `unknown`, `blocked`, `unverified`, and `manual-review` states;
  never turn missing evidence into a positive capability claim.
- Use fixed inputs and sorted JSON for tests, snapshots, and safety reports.
