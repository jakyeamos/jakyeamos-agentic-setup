# Case study: repository-aware routing

## Problem

Agents often mix governing instructions, stale project state, stable reference
material, and raw evidence. Broad workspace scans then increase noise and may
expose private infrastructure that was never part of the task.

## Mechanism

`repo-aware-context` separates policy, truth, reference, evidence, and handoff.
It routes from the exact repository and branch, follows the nearest context
index, searches for existing behavior, and loads only the minimum useful
context. The source map makes external and excluded material visible without
turning it into a copyable asset.

## Evidence

The audit found reusable patterns across several agent hosts but also found
machine-specific instructions, managed files, generated indexes, and private
runtime stores. The catalog records those sources as adapters or external
references and keeps the packaged entrypoints vendor-neutral.

## Limitation

The workflow reduces scope ambiguity by policy; it does not prove that an
agent selected the best context. Selection quality still needs task-level
review and measured evaluation.
