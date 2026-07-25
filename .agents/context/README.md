# Repository context index

`last_reviewed: 2026-07-25`

Read this index before non-trivial work. Load only the packet that matches the
task; do not dump the catalog, fixtures, generated state, or private runtime
artifacts into context.

- [Architecture and boundaries](architecture.md)
- [Canonical commands and quality gates](commands.md)
- [Coding and catalog conventions](conventions.md)
- [Security and approval constraints](security.md)
- [Common failure modes and recovery](failure-modes.md)
- [Canonical implementation examples](examples.md)
- [Definition of done](done.md)
- [Packaging and rollback](deployment.md)

The root `AGENTS.md` contains hard invariants and routing pointers. The
machine-readable `.pre-cr.json` contract and
`scripts/check_environment_contract.mjs` are authoritative for freshness,
quality commands, approval boundaries, and tracked-path checks.
