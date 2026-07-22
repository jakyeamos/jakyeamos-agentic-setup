# Attribution and provenance

The Portable Agentic Workbench is authored and curated by Jakye Amos and is
released under the MIT license in this repository.

## Packaged assets

- `research-domain-writing` is retained at its existing path as a portable
  skill. It may use the optional external `rdw` CLI when installed.
- `terrace` is retained at its existing path as a portable router skill. It
  routes through the external `terrace` CLI.
- The context, routing, safety, evaluation, and handoff workflows are authored
  or sanitized behavioral patterns in this repository.
- The nine additive skills introduced in catalog `0.3.0` are sanitized,
  first-party behavioral patterns mined from authored workflows and local skill
  sources. Private source paths, generated harvests, and host registrations are
  not redistributed.
- Vendor adapters are behavioral mappings only. They do not redistribute
  managed host configuration, private hooks, session state, or binaries.
- The `agent-config` engine and public manifest contract are sanitized,
  first-party behavioral mining from the private instruction-migration
  companion. The companion's concrete manifest, live mappings, audit evidence,
  and conflict ledger are not redistributed.

## External references

The catalog links to AIOS, TMCP, Quality Runner, agent-eval-contract, and
context-compiler-contract as separate projects. Their runtimes, generated
harvests, caches, and contract implementations are not copied here. Read the
corresponding `external` record in `catalog/manifest.json` before adapting a
reference.

## Source classes

Every catalog record declares one of these classes:

- `portable`: safe to copy under the declared license and install mode;
- `adapter`: target-specific guidance staged for manual review;
- `case-study`: evidence and design narrative only;
- `external`: linked project, not copied;
- `excluded`: private, generated, vendor-owned, or unsafe material.

The manifest is the authoritative source map. Logical source names are used in
place of personal machine paths and runtime snapshots.

The macOS build/release donor material remains deferred from the public catalog
until license and redistribution evidence is complete; no donor files are
copied by this release.
