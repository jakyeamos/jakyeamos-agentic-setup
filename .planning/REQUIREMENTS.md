# Requirements: jakyeamos-agent-skills

**Defined:** 2026-07-04
**Core Value:** Make recurring agent failure modes portable, explainable, and verifiable while preserving the separate QR track.

## v1 Requirements

### QR Remediation

- [ ] **QR-JAKYEAMOS-AGENT-SKILLS**: Resolve the Quality Runner advisory clusters from run qr-low-risk-post-branch-fix-20260704-jakyeamos-agent-skills for jakyeamos-agent-skills without changing intended behavior, then verify with focused repo checks and a post-remediation QR comparison.

### Portable Agentic Workbench

- [x] **WB-CATALOG**: Maintain a versioned manifest with asset classes, provenance, license status, targets, entrypoints, dependencies, evidence, and install mode.
- [x] **WB-INSTALLER**: Provide deterministic list, search, show, validate, and dry-run-by-default install commands with explicit roots, no overwrites, dependency reporting, and manual adapter staging.
- [x] **WB-PUBLIC-SAFETY**: Reject private paths, credential material, environment files, raw authorization values, and unsafe artifacts in distributable surfaces.
- [x] **WB-NARRATIVE**: Document the hiring-manager narrative, agent mining workflow, evidence case studies, vendor adapters, external boundaries, and limitations without unsupported performance claims.

## v2 Requirements

### Fleet Quality

- **QR-FLEET-BASELINE**: Keep this repo in the recurring QR fleet once the initial remediation phase closes.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Broad rewrite | QR remediation should stay clustered and behavior-preserving. |
| QR execution | Quality Runner is advisory-only. |
| Private runtime packaging | AIOS, TMCP, Quality Runner, external contracts, managed host configuration, session data, logs, and generated harvest output stay excluded or linked. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| QR-JAKYEAMOS-AGENT-SKILLS | Phase 1 | Pending |
| WB-CATALOG | Phase 2 | Complete |
| WB-INSTALLER | Phase 2 | Complete |
| WB-PUBLIC-SAFETY | Phase 2 | Complete |
| WB-NARRATIVE | Phase 2 | Complete |

**Coverage:**
- v1 requirements: 5 total
- Mapped to phases: 5
- Unmapped: 0

---
*Requirements defined: 2026-07-04*
*Last updated: 2026-07-21 after Portable Agentic Workbench phase addition*
