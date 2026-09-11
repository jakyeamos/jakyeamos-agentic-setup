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
contract. Its JSON output includes the measured context review age and freshness
limit. An applicable agent-usability contract must provide at least one
existing behavior-evidence file for every declared tool. The focused validator
is also executable with `node scripts/check_agent_usability.mjs`.

The report-only CLI commands are `pnpm audit`, `pnpm doctor`, `pnpm drift`, and
`pnpm smoke`. `sync`, `install`, `uninstall`, and `bootstrap` remain
dry-run/manual-review surfaces; `--apply` requires an explicit target and a
reviewed plan. Workbench `uninstall --apply` removes only files recorded in an
installer-owned receipt and refuses modified, symlinked, or unowned targets.
`agent-config sync --provider <runtime> --root <repository> --dry-run --json`
previews only the selected runtime entries from that repository's manifest.
Unknown subcommands fail with a pointer to `agent-config --help`.

Quality commands must remain bounded, deterministic, offline-capable, and
free of provider, login, deployment, merge, push, migration, or deletion work.

Compass proof receipts are machine-local runtime data only when they use the
producer schema under `.project-compass/evidence/` and Git confirms they are
ignored and untracked. Public safety continues scanning tracked, malformed,
unowned, and non-Git receipts; force-adding a receipt never exempts it.

For intent-preserving development, start with `project_compass.py family . --summary --json`, then prepare a bounded `change-context`. See the Compass skill's cumulative `--continue` workflow and linked bootstrap contract; never reuse a blocked packet as accepted intent.

Design reassessment uses the existing Compass assess command with v2 proposals. See skills/project-compass/references/assessment.md; complete fields never establish justification without current claim review.

Broad Compass reconciliation can explicitly write a complete eligible packet with `change-context --packet-output .quality-runner/compass/reconciled.json`; inspect it before adoption. See the skill development reference for the distinct artifact and gate-summary schemas.

Compass hashes source references up to 16 MiB in bounded chunks; parsed JSON remains capped at 1 MiB. See the development reference for unchanged packet and artifact limits. Binary identity does not establish media playback or visual acceptance.
