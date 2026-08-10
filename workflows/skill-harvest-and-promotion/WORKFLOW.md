# Skill Harvest and Promotion

Use this workflow to mine authored workflows and instructions for polished, portable skills without copying private implementation detail.

## 1. Select sources

Prefer first-party authored repositories, local skill directories, durable workflow documents, and tested operational instructions. Exclude generated graphs, caches, transcripts, runtime stores, credentials, vendor-managed content, product secrets, and domain material that cannot be redistributed.

For each source, record a logical source class and evidence label. Do not publish private paths, raw excerpts, identifiers, or environment-specific configuration.

## 2. Extract behavior atoms

Reduce a source to reusable atoms:

- trigger and non-trigger conditions;
- inputs, outputs, and stopping conditions;
- decision points and status transitions;
- safety boundaries and approval gates;
- verifiers, fixtures, and failure behavior;
- dependencies and supported targets.

Keep the behavior, not the source's personal vocabulary or repository scaffolding.

## 3. Deduplicate and sanitize

Compare the atoms with the existing public catalog. Merge overlapping guidance into the strongest existing skill. Remove private paths, secret-shaped values, host-specific commands, product names that are not needed, and claims that cannot be verified. Preserve provenance as a sanitized logical label.

## 4. Use the promotion gate

Promote only when the candidate has a reusable trigger, clear non-triggers, a decision path, safety boundaries, a verifier, and a clean-room-testable output. Otherwise record `merged`, `external-reference`, `deferred`, or `excluded` with a reason in the private disposition ledger.

## 5. Validate the package

Author a concise `SKILL.md`, a supporting workflow or reference, and a fixture when the contract benefits from structured validation. Forward-test one triggering and one non-triggering scenario. Run the public safety scan, manifest validation, link checks, and a disposable install. The result is not promoted until every referenced file exists and no private provenance leaks.

## 6. Admit leverage candidates

When the source is `ai-workflow-leverage`, keep the private
`leverage-promotion-candidate/v1` packet separate from the JAS package. A
portable or adapter candidate uses a sanitized `jas-promotion-projection/v1`
with public asset metadata. A reference-only candidate may use the same v1
projection when it is represented as an `external` asset with at least one
public URL; JAS records the relationship and manual-review boundary without
copying the external runtime. A private-only candidate must carry the sanitized
`private_package` descriptor and use `jas-promotion-projection/v2`; its
projection contains only the private asset's safe metadata, artifact reference,
relative package paths, and symbolic install destination. Run
`pnpm promotion-admission validate` and `plan`. After human review, run
`admit` with a `jas-promotion-approval/v1` document. The command emits either a
manifest-review plan or a private-overlay review plan and never edits
`catalog/manifest.json` or writes an overlay file itself.

For a private-only result, review the emitted `jas-private-overlay/v2`, keep it
outside this repository, and resolve it with `pnpm agent-config overlay`. To
stage the actual sanitized package into a disposable target, run
`pnpm agent-config overlay-install --overlay <path> --private-root <path>
--root <disposable-target> --dry-run`, then repeat with `--apply` only after
review. The installer requires every declared package file, blocks on existing
targets, and never overwrites. A v1 private-overlay projection remains a
legacy blocked form rather than silently becoming public parity.

See [the skill contract](../../skills/skill-harvest-and-promotion/SKILL.md) and the [sanitized mining report](../../docs/mining/2026-07-public-skill-mining.md).
