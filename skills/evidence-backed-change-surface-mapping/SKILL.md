---
name: evidence-backed-change-surface-mapping
description: Use when a requested change may affect linked repositories, generated artifacts, trackers, validation contracts, or external projections and the impact map must remain advisory and evidence-backed.
---

# Evidence-Backed Change-Surface Mapping

Use this skill to discover likely owners, source-of-truth files, dependent
surfaces, validation commands, and unresolved dependencies before editing.

Do not treat an inferred edge as authority, a stale map as current, or an
unknown path as safe to ignore.

## Contract

1. Identify repository identity separately from checkout and branch state.
2. Discover bounded source surfaces, history patterns, references, owners, and
   validation commands.
3. Emit surfaces, observations, edges, patterns, and assessments with
   evidence, confidence, freshness, and provenance.
4. Cap scans and graph edges; preserve truncation and unknown paths visibly.
5. Suggest reads and checks without mutating the target checkout.
6. Give every inferred edge a removal condition or mark it unresolved.

## Output

Return matched surfaces, suggested reads, validation commands, owners, unknown
paths, unresolved dependencies, freshness state, evidence references, and the
confidence-limited next action.

See the [change-surface workflow](../../workflows/evidence-backed-change-surface-mapping/WORKFLOW.md).
