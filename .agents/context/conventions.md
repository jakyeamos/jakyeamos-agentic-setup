# Coding and catalog conventions

- Use Node ESM with explicit imports and standard-library APIs in the runtime.
- Use Python 3 with annotations and deterministic, sorted validator output.
- Treat `catalog/manifest.json` as the machine-readable entry and installation
  source of truth and `catalog/taxonomy.json` as the source of truth for entry
  types and curated collections.
- Generate `catalog/index.md` with `workbench.py index --write`; do not maintain
  a second catalog roster in README or other prose.
- Put newly authored entries in `library/<type>/<slug>/`. Keep topics and use
  cases in metadata because they are many-to-many.
- Preserve stable asset IDs, schema versions, provenance classes, supported
  targets, and install modes. Changes to those fields require fixture coverage.
- Keep always-loaded files limited to invariants and routing pointers. Put
  procedures, examples, and host-specific details in routed packets.
- Preserve `unknown`, `blocked`, `unverified`, and `manual-review` states;
  never turn missing evidence into a positive capability claim.
- Use fixed inputs and sorted JSON for tests, snapshots, and safety reports.
