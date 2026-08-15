# Agent-config manifest contract

`manifest.yaml` is a public, JSON-compatible YAML template. It describes
ownership and routing without embedding a machine's live instruction files.
Use an explicit `--manifest` path for a private companion configuration.

## Required entry fields

Every entry declares `id`, `source`, `destination`, `owner`, `runtime`, `layer`,
`always_loaded`, `path_kind`, `sync_direction`, `provenance`,
`install_recipe`, and `status`.

Paths use symbolic roots such as `$MANIFEST_ROOT` and `$HOME`; absolute host
paths, home shorthands, parent traversal, credentials, and secret-shaped values
are rejected. The engine records file, directory, and symlink snapshots. A
symlink snapshot includes its link target so provenance is visible without
following the link.

## Layers and states

Use `global-invariants`, `global-routing`, `runtime-adapter`, `repo-context`,
`module-context`, and `on-demand` in descending specificity. Always-loaded
entries may only carry hard stops and routing pointers. Line count is reported
as evidence, not a numeric gate.

Snapshot comparison distinguishes `equal`, `repo-only`, `live-only`,
`repo-modified`, `live-modified`, `both-modified`, and `diverged-no-baseline`.
Unknown live members and missing targets are preserved as visible findings.

## Commands

```text
agent-config audit|drift|doctor|sync|install|bootstrap|smoke|overlay|overlay-install
```

Commands are report-only by default. `sync` and `install` require both an
explicit manifest and `--apply`; the full preflight must be clear, and writes
are allowed only to missing explicit targets. `--allow-broad-scan` is required
for a scope rooted at `$HOME`. No command handles credentials, login, CAPTCHA,
MFA, or GUI-only setup.

For an audit-only provider plan, use
`agent-config sync --manifest <repo>/manifest.yaml --provider codex --dry-run
--json` (or `--manifest` with the equivalent source path). The result is a
plan only: it reports `execution_mode: "dry-run"`,
`projection_status: "not_projected"`, and `mutated: false`; it is not evidence
that a provider projection or live sync occurred. Persistent overlay work is
similarly report-only unless the explicit disposable root and `--apply`
authority are both present.

## Private companion overlay

`agent-config overlay --overlay <path>` resolves a private
`jas-private-overlay/v1` or `jas-private-overlay/v2` file against the public
catalog. The file is kept outside the repository. v1 contains references to
eligible public `portable` or `adapter` assets; v2 may also contain sanitized
private asset metadata and relative package paths. The package bytes are never
embedded in the overlay and are supplied separately through `--private-root`.
Absolute host paths, parent traversal, home shorthands, unknown assets,
unsupported target mappings, and non-redistributable catalog classes are
rejected.

The command is report-only and does not edit `catalog/manifest.json`, the
overlay, or live target files. Normal `agent-config` commands without an
overlay operate on the public base; `agent-config overlay --overlay <path>` is
the personal-base-plus-overlay mode. The overlay contract is defined in
[`schemas/jas-private-overlay.schema.json`](../schemas/jas-private-overlay.schema.json).

`agent-config overlay-install --overlay <path> --private-root <path> --root
<disposable-target>` builds the installation plan for enabled public and
private assets. It is report-only by default. `--apply` is allowed only after
the full plan is clear; any existing target or missing source blocks the whole
plan, and the command never overwrites files. `$HOME` destinations are mapped
inside the explicit target root, so the command does not write to the running
machine's home directory.
