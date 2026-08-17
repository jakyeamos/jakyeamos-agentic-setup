# Canonical commands and quality gates

Run from the repository root with the pinned pnpm toolchain:

```sh
pnpm install --offline --frozen-lockfile --trust-lockfile --ignore-scripts --prod=false
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm check
python3 scripts/pre_cr_coverage.py
```

`pnpm lint` runs catalog, skill, prevention-pack, and public-safety checks.
`pnpm typecheck` syntax-checks every tracked JavaScript module. `pnpm build`
validates the catalog as the packaging surface. `pnpm check` validates the
environment contract, including routed packets, freshness, strict scripts,
the required Pre-CR adapter, tracked secret-like paths, and the agent-usability
contract. An applicable agent-usability contract must provide at least one
existing behavior-evidence file for every declared tool. The focused validator
is also executable with `node scripts/check_agent_usability.mjs`.

The report-only CLI commands are `pnpm audit`, `pnpm doctor`, `pnpm drift`, and
`pnpm smoke`. `sync`, `install`, `uninstall`, and `bootstrap` remain
dry-run/manual-review surfaces; `--apply` requires an explicit target and a
reviewed plan. Workbench `uninstall --apply` removes only files recorded in an
installer-owned receipt and refuses modified, symlinked, or unowned targets.

Quality commands must remain bounded, deterministic, offline-capable, and
free of provider, login, deployment, merge, push, migration, or deletion work.
