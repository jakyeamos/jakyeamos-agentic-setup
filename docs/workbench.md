# Workbench manual

This page owns the technical setup and safety contract. The root README is the
editorial cover; the generated catalog is the inventory.

## Inspect and adopt a multiplier

The Python catalog CLI uses only the standard library:

```bash
python3 scripts/workbench.py list --type skill
python3 scripts/workbench.py search --query "long context" --json
python3 scripts/workbench.py show context-budget-governor --json
python3 scripts/workbench.py install context-budget-governor \
  --target generic --root /tmp/workbench-target --dry-run --json
```

Installation requires an explicit target root, defaults to dry-run, copies
only manifest-allowlisted files, and never overwrites an existing file. It
reports external dependencies but does not install them. Adapters are staged
for review; external references remain manual and are never copied.

## Manifest-aware setup engine

The dependency-light Node engine handles explicit, fail-closed configuration
work:

```bash
pnpm agent-config --help
pnpm audit -- --json
pnpm drift -- --json
pnpm doctor -- --json
pnpm sync -- --dry-run --json
pnpm agent-config install --dry-run --json
pnpm bootstrap -- --dry-run --json
pnpm smoke -- --json
```

Pass `--manifest <path>` to select a manifest, `--apply` only after reviewing
the plan, and `--allow-broad-scan` only with explicit approval. The engine does
not overwrite existing targets, delete unknown live members, resolve
unresolved conflicts, or handle credentials, login, CAPTCHA, MFA, or GUI-only
setup.

## Promotion admission

`ai-workflow-leverage` owns private discovery, testing, quantification, and the
`leverage-promotion-candidate/v1` packet. This repository consumes a sanitized
projection at an admission boundary; it never copies private evidence, paths,
runtime details, or package content into a public catalog plan.

Report-only commands validate and plan an admission:

```bash
pnpm promotion-admission validate \
  --candidate /path/to/leverage-candidate.json \
  --projection /path/to/jas-public-projection.json --json
pnpm promotion-admission plan \
  --candidate /path/to/leverage-candidate.json \
  --projection /path/to/jas-public-projection.json --json
pnpm promotion-admission admit \
  --candidate /path/to/leverage-candidate.json \
  --projection /path/to/jas-public-projection.json \
  --approval /path/to/jas-approval.json --json
```

New portable, adapter, and reference-only candidates use
`jas-promotion-projection/v3`. Its public asset must include complete
`editorial` metadata: `type`, non-empty `topics`, non-empty `use_cases`, `why`,
`use_when`, and `avoid_when`. This makes every newly admitted multiplier
browsable without a later curation pass. Legacy public v1 packets remain
accepted for compatibility. Reference-only candidates must still project as
`external` with at least one public URL and remain manual. Private-only v2
candidates produce a private-overlay review plan whose package content stays
in a separately supplied private root. All report-only commands return
`mutated: false`.

After owner acceptance, the explicit apply boundary is:

```bash
pnpm promotion-admission apply \
  --candidate /path/to/leverage-candidate.json \
  --approval /path/to/jas-approval.json \
  --mode public --root /absolute/path/to/jakyeamos-agentic-setup \
  --apply --json
```

Apply validates and preflights before mutation, remains idempotent, and reports
`JAS_APPLIED` or `JAS_ALREADY_APPLIED`. `defer` and `reject` never reach it.
See [`schemas/jas-promotion-projection.schema.json`](../schemas/jas-promotion-projection.schema.json)
for the projection contract.

## Public base and private overlay

The public catalog is the distribution base. A personal machine can resolve a
separate v1 or v2 JSON overlay kept outside this repository:

```bash
pnpm agent-config overlay \
  --overlay "$HOME/.config/jas/private-overlay.json" --json
pnpm agent-config overlay-install \
  --overlay "$HOME/.config/jas/private-overlay.json" \
  --private-root "$HOME/.config/jas/private-packages" \
  --root /tmp/jas-target --dry-run --json
```

The resolver checks workbench identity, eligibility, target support, and
symbolic path safety without editing either source. Overlay installation
refuses missing sources, existing targets, unsafe symlinks, and partial
preflight plans. The schema is
[`schemas/jas-private-overlay.schema.json`](../schemas/jas-private-overlay.schema.json).

## Validation

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm check
python3 scripts/pre_cr_coverage.py
```

The tests use disposable directories and do not require a provider runtime or
external project. Builds and validators prove packaging and contract behavior;
they do not prove model-quality gains or host parity. See the case studies and
[`docs/external-references.md`](external-references.md) for evidence and
ownership boundaries.
