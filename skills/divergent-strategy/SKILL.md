---
name: divergent-strategy
description: Use when multiple plausible strategies exist and the decision needs candidate generation, independent judging, portfolio selection, uncertainty, and approval-gated promotion.
---

# Divergent Strategy

Use this skill for architecture, workflow, product, prompt, or standards
decisions where premature convergence would hide meaningful alternatives.

Do not use it for a deterministic small fix or when acceptance criteria already
select one implementation.

## Contract

1. Classify the decision and select a bounded exploration mode.
2. Generate a candidate portfolio with explicit assumptions and failure modes.
3. Judge candidates against named criteria with rationale and uncertainty. When
   the decision supplies measurable criteria (for example time, cost, risk,
   or coverage), score every supplied criterion for every candidate; do not
   silently replace it with a convenient proxy or invented weighting.
4. Select a portfolio or recommendation, not merely an attractive first idea.
5. Record entropy, rejected options, and unresolved product or environment
   questions.
6. Propose memory, prompt, skill, or workflow writebacks separately from the
   recommendation and require approval before promotion.

See the [strategy workflow](../../workflows/divergent-strategy/WORKFLOW.md).
