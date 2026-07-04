# Phase 1: QR remediation: jakyeamos-agent-skills - Context

**Gathered:** 2026-07-04
**Status:** Ready for planning
**Source:** PRD Express Path (/Users/jakyeamos/.local/state/quality-runner/fleet/per-repo-summaries-20260704/jakyeamos-agent-skills.md)

<domain>
## Phase Boundary

Plan the remediation work for jakyeamos-agent-skills from Quality Runner run qr-low-risk-post-branch-fix-20260704-jakyeamos-agent-skills.
This phase is planning-only until execute-phase runs. Quality Runner remains advisory-only: it identifies findings, remediation clusters, and verification suggestions, but all source changes happen in /Users/jakyeamos/projects/jakyeamos-agent-skills.

Findings: 8
Severity: `blocker` 5, `warning` 3
Categories: `capability` 8
Fleet phase candidate: Phase 2 - Capability Baselines
Requirement: QR-JAKYEAMOS-AGENT-SKILLS

</domain>

<decisions>
## Implementation Decisions

### D-01 - QR summary is the planning source
- Use /Users/jakyeamos/.local/state/quality-runner/fleet/per-repo-summaries-20260704/jakyeamos-agent-skills.md and the artifacts under /Users/jakyeamos/projects/jakyeamos-agent-skills/.quality-runner/runs/qr-low-risk-post-branch-fix-20260704-jakyeamos-agent-skills as the source of truth for this remediation phase.

### D-02 - Cluster-oriented remediation
- Plan and execute coherent remediation batches by QR cluster, not one isolated edit per finding row.

### D-03 - Behavior preservation
- Prefer behavior-preserving refactors, hardening, and simplification. Do not change product behavior unless a QR hardening cluster explicitly requires safer behavior.

### D-04 - Existing project conventions first
- Read the target files and local manifests before editing. Follow existing package-manager, formatter, test, and architecture conventions. Use pnpm for JavaScript package scripts.

### D-05 - Evidence-backed closure
- A cluster is done only when focused repo verification passes and a post-remediation QR run shows the fingerprints cleared or are dispositioned with evidence.

### Claude's Discretion
- Choose exact helper extraction boundaries, naming, and task order when the QR document identifies the finding but not the implementation shape.
- If a cluster turns out to require product, API, or design decisions, stop that cluster and capture the question instead of guessing.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Quality Runner Inputs
- `/Users/jakyeamos/.local/state/quality-runner/fleet/per-repo-summaries-20260704/jakyeamos-agent-skills.md` - Per-repo QR summary used as this phase PRD.
- `/Users/jakyeamos/projects/jakyeamos-agent-skills/.quality-runner/runs/qr-low-risk-post-branch-fix-20260704-jakyeamos-agent-skills/quality-audit.json` - Quality audit report.
- `/Users/jakyeamos/projects/jakyeamos-agent-skills/.quality-runner/runs/qr-low-risk-post-branch-fix-20260704-jakyeamos-agent-skills/remediation-plan.json` - QR remediation plan.
- `/Users/jakyeamos/projects/jakyeamos-agent-skills/.quality-runner/runs/qr-low-risk-post-branch-fix-20260704-jakyeamos-agent-skills/code-quality-scan.json` - Code-quality scan fingerprints.
- `/Users/jakyeamos/projects/jakyeamos-agent-skills/.quality-runner/runs/qr-low-risk-post-branch-fix-20260704-jakyeamos-agent-skills/resolution-ledger.md` - Resolution ledger for closure evidence.
- `/Users/jakyeamos/projects/jakyeamos-agent-skills/.quality-runner/runs/qr-low-risk-post-branch-fix-20260704-jakyeamos-agent-skills/agent-handoff.md` - QR agent handoff.

</canonical_refs>

<specifics>
## Top Findings

- `missing-dead-code` blocker capability: Required quality capability is missing: dead_code. Fix: Add a dead-code scan command such as pnpm audit:dead-code. Evidence: Capability map lists dead_code as missing.; Missing command capability evidence: no quality command found for dead_code.
- `missing-formatter` blocker capability: Required quality capability is missing: formatter. Fix: Add a formatter command such as pnpm format. Evidence: Capability map lists formatter as missing.; Missing command capability evidence: no quality command found for formatter.
- `missing-lint` blocker capability: Required quality capability is missing: lint. Fix: Add a lint command such as pnpm lint. Evidence: Capability map lists lint as missing.; Missing command capability evidence: no quality command found for lint.
- `missing-tests` blocker capability: Required quality capability is missing: tests. Fix: Add a test command such as pnpm test. Evidence: Capability map lists tests as missing.; Missing command capability evidence: no quality command found for tests.
- `missing-typecheck` blocker capability: Required quality capability is missing: typecheck. Fix: Add a typecheck command such as pnpm typecheck. Evidence: Capability map lists typecheck as missing.; Missing command capability evidence: no quality command found for typecheck.
- `missing-build` warning capability: Required quality capability is missing: build. Fix: Add a build command such as pnpm build. Evidence: Capability map lists build as missing.; Missing command capability evidence: no quality command found for build.
- `missing-pre-pr` warning capability: Required quality capability is missing: pre_pr. Fix: Add a pre-PR check command or document the equivalent release gate. Evidence: Capability map lists pre_pr as missing.; Missing command capability evidence: no quality command found for pre_pr.
- `missing-runtime-smoke` warning capability: Required quality capability is missing: runtime_smoke. Fix: Add a smoke-test command for runtime verification. Evidence: Capability map lists runtime_smoke as missing.; Missing command capability evidence: no quality command found for runtime_smoke.

## Remediation Clusters

No active remediation clusters; preserve the zero-finding baseline and verify QR stays clean.

</specifics>

<deferred>
## Deferred Ideas

- Broad rewrites outside the QR clusters.
- Running Quality Runner as an executor or letting QR mutate source code.
- Remediating repos outside jakyeamos-agent-skills; each repo gets its own GSD phase.

</deferred>

---

*Phase: 1*
*Context gathered: 2026-07-04 via QR per-repo PRD*
