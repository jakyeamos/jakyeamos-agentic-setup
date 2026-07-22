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
agent-config audit|drift|doctor|sync|install|bootstrap|smoke
```

Commands are report-only by default. `sync` and `install` require both an
explicit manifest and `--apply`; the full preflight must be clear, and writes
are allowed only to missing explicit targets. `--allow-broad-scan` is required
for a scope rooted at `$HOME`. No command handles credentials, login, CAPTCHA,
MFA, or GUI-only setup.
