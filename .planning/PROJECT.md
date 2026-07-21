# jakyeamos-agent-skills

## What This Is

jakyeamos-agent-skills is an existing local codebase in Jakye's QR remediation fleet. This GSD project was initialized from Quality Runner documentation so remediation can be planned, executed, verified, committed, and pushed in atomic repo-local phases.

## Core Value

Make recurring agent failure modes portable, explainable, and verifiable while
keeping the existing Quality Runner remediation track separate.

## Requirements

### Validated

- Existing repository behavior is the baseline unless a QR hardening finding requires safer input handling.

### Active

- [ ] Resolve QR findings from run qr-low-risk-post-branch-fix-20260704-jakyeamos-agent-skills using cluster-oriented remediation.
- [ ] Verify remediation with focused repo checks and post-remediation QR comparison.
- [ ] Keep QR advisory-only; source changes happen through GSD execution and git commits.
- [ ] Package the Portable Agentic Workbench catalog, installer, adapters, case studies, and clean-room evidence.

### Out of Scope

- Broad rewrites outside the QR clusters.
- Pulling QR into execution/mutation responsibilities.
- Changing product/API/design behavior without an explicit QR hardening need or user decision.

## Context

- Repo path: this repository checkout
- QR summary: external Quality Runner per-repository summary for this package
- QR run directory: local Quality Runner baseline artifact for the separate QR phase
- Existing package: dependency-free Python skill package with Research Domain Writing and Terrace.
- New packaging source of truth: `catalog/manifest.json`.
- Public boundary: portable assets and sanitized adapters only; private runtime, generated harvests, and external runtimes remain excluded or linked.

## Constraints

- **Git:** Commit in atomic units scoped to this repo and concern.
- **Verification:** A cluster is complete only with focused checks plus QR comparison evidence.
- **Package management:** Use pnpm for JavaScript package scripts.
- **Packaging:** Keep the runtime dependency-free and require explicit installer target roots.
- **Planning:** Add the workbench as Phase 2; do not rewrite the existing QR-remediation Phase 1.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use QR per-repo summaries as PRDs | They contain the current finding clusters, artifacts, and verification suggestions. | Pending execution |
| Keep Quality Runner advisory-only | The user explicitly does not want execution pulled into QR. | Good |

---
*Last updated: 2026-07-04 after QR remediation GSD bootstrap*
