---
name: skill-harvest-and-promotion
description: Use when mining agent skills, rules, workflow docs, or repeated operating behavior and deciding what should become a portable public skill.
---

# Skill Harvest and Promotion

Use this skill to turn a local corpus into a small, evidence-backed promotion
set. It is a discovery and packaging workflow, not an instruction to copy a
repository wholesale.

Do not use it to implement the underlying product change or to promote a
preference that has no observable behavior, verifier, or safety boundary.

## Contract

1. Select the smallest useful source set and record source ownership.
2. Harvest behavior atoms, trigger language, outputs, failure modes, and
   evidence tiers.
3. Redact private paths, credentials, raw transcripts, runtime state, and
   vendor-managed material before producing shared artifacts.
4. Compare candidates against existing skills and merge overlapping behavior.
5. Classify every candidate as promote, strengthen, reference, defer, or
   exclude with a reason.
6. Author a concise triggerable skill plus supporting workflow material.
7. For a public JAS handoff, provide complete editorial metadata: multiplier
   type, topics, use cases, why it matters, when to use it, and when not to.
8. Forward-test trigger and non-trigger scenarios, then promote only when the
   package is portable and objectively verifiable.

## Promotion gate

A promotion candidate needs a reusable trigger, non-trigger, input/output
contract, decision path, safety boundary, verifier, stopping condition, and
clean-room fixture. A complete high-leverage workflow may qualify from one
strong implementation when its cross-runtime reuse is clear; record that
exception explicitly.

## Output

Return source and skip lists, redaction warnings, behavior atoms, duplicate
analysis, the disposition ledger, the package files, evidence gaps, and the
forward-test results.

See the [harvest workflow](../../workflows/skill-harvest-and-promotion/WORKFLOW.md).
