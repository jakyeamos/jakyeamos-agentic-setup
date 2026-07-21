# Portable Agentic Workbench: mining guide

This repository is a public, vendor-neutral catalog of agent workflows,
portable skills, sanitized adapters, and evidence. It is not a snapshot of a
private agent runtime.

## Mining contract

1. Start with [`catalog/manifest.json`](catalog/manifest.json). Treat it as the
   source of truth for asset identity, maturity, targets, files, dependencies,
   provenance, evidence, and installation mode.
2. Use the dependency-free CLI before reading the whole tree:

   ```bash
   python3 scripts/workbench.py list --json
   python3 scripts/workbench.py search --query "long context" --json
   python3 scripts/workbench.py show context-budget-governor --json
   ```

3. Read the asset's entrypoint and its evidence references. Distinguish
   observed evidence from hypotheses and limitations.
4. Use `install ... --dry-run` with an explicit disposable root before any
   apply operation. An adapter is staged for manual review; it is never
   registered implicitly.
5. Run `python3 scripts/workbench.py validate` after proposing a mapping.

## Safety boundary

Do not search for or import private transcripts, credentials, environment
files, session databases, AIOS logs, generated harvests, or host-managed
configuration. The manifest's `external` and `excluded` records are links and
boundary notes, not invitations to copy runtime material.

## Recommendation format

When recommending an asset to another agent, report:

- the asset ID and target;
- the problem it addresses and the mechanism it uses;
- the provenance and license status;
- the evidence reference and what was actually observed;
- dependencies and installation mode;
- limitations, including any manual adapter step.

For the full inspection sequence, read [`docs/mining.md`](docs/mining.md).
For a human overview, read [`catalog/index.md`](catalog/index.md).
