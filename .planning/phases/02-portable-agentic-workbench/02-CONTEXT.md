# Phase 2: Portable Agentic Workbench - Context

**Gathered:** 2026-07-21
**Status:** Implementing

## Domain

Expand the existing public two-skill package into a curated, vendor-neutral
catalog that another agent can mine safely and a hiring manager can understand.
The catalog is the source of truth; private runtime infrastructure and
external project runtimes remain outside the package.

## Decisions

- Keep the repository name `jakyeamos-agent-skills` and product identity
  `Portable Agentic Workbench`.
- Keep MIT licensing and dependency-free runtime scripts.
- Preserve `skills/research-domain-writing` and `skills/terrace` unchanged in
  their existing locations.
- Use portable, adapter, case-study, external, and excluded source classes.
- Make installer writes explicit, dry-run by default, no-overwrite, and
  manual-review for adapters and hook-shaped mappings.
- Keep Gemini as a catalog-only reference in v1.
- Do not copy AIOS, TMCP, Quality Runner, agent-eval-contract, or
  context-compiler-contract runtimes.

## Evidence and limits

The repository audit found reusable context, routing, guard, evaluation, and
handoff patterns across several agent hosts, alongside machine-specific and
managed material. The packaged case studies describe those observations and
label hypotheses and limitations. No model-quality improvement is claimed
without a measured baseline.

## Boundary

This phase adds packaging work. The existing QR-remediation Phase 1 remains a
separate planning track and is not rewritten here.
