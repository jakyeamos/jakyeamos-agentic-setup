# Public JAS system map

Status: proposal catalog; no child Compass has been ratified from this map.

## Decision record

- Selected form: ICM System map. Public JAS combines catalog identity,
  portable authoring contracts, host adapters, and a manifest/runtime engine.
- Rejected smaller form: root context alone. The public/private and
  source/projection boundaries need explicit impact routing.
- Authority: the root Compass and repository architecture context define
  public intent; this map does not create a second catalog authority.
- Current user gate: `jas-public-boundary-realignment-20260824` is unanswered
  and draft-only.

## Universe inventory

- **live candidates:** `catalog/`, `library/`, `skills/`, `workflows/`,
  `adapters/`, `bin/`, `src/`, `schemas/`, `scripts/`, and tests.
- **source layers:** docs, templates, and fixtures are mapped as support or
  contract inputs unless they own an independent product outcome.
- **unknown:** the exact child grouping and the boundary between portable
  contracts and adapter guidance.
- **ghost:** no ghost implementation is asserted here.

## Proposed target tree

```text
map/
├── AGENTS.md
├── CONTEXT.md
├── _meta/schema.md
├── _templates/object.md
└── objects/
    ├── CONTEXT.md
    └── _index.md
```

Candidate clusters:

- **catalog-and-taxonomy** — manifest identity, provenance, targets, and
  catalog projection.
- **portable-contracts** — library, skill, workflow, template, and portable
  contract surfaces.
- **host-adapters** — provider/host-specific integration guidance and code.
- **manifest-runtime-and-verification** — schema, CLI/runtime, validation,
  scripts, and tests.

## Migration and ownership map

The current root Compass remains the only active Compass. No public catalog,
private package, installed projection, or provider configuration is changed by
this map. The private companion remains outside the public tree.

## First-order impact

- **Hits:** changes to manifest identity, portable contract shape, adapter
  boundaries, or validation/runtime behavior hit the corresponding cluster and
  may require projection review.
- **Does not hit:** changing a private overlay or installed projection does not
  make it public source truth.

## Open decisions

1. Which four surfaces deserve independent child Compasses?
2. Which adapter behavior is evidence-only versus portable contract?
3. What evidence is required before a catalog projection is admitted?

