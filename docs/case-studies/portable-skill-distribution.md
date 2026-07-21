# Case study: portable skill distribution

## Problem

A personal agent setup can contain valuable workflow knowledge alongside host
configuration, managed vendor files, private histories, and machine-specific
paths. Copying the whole setup makes reuse unsafe and makes the capability hard
for another agent or a hiring manager to inspect.

## Mechanism

The workbench keeps the existing `research-domain-writing` and `terrace` skill
paths backward-compatible, adds a versioned manifest, and classifies every
asset as portable, adapter, case-study, external, or excluded. Provenance and
license status travel with each record. The installer copies only allowlisted
files and stages adapters for manual review.

## Evidence

The original two-skill package already passed its dependency-free skill
validator. The expanded package preserves that validator, adds catalog and
public-safety validation, and has deterministic list/search/show/install
surfaces plus a clean-room test path.

## Limitation

Portability is demonstrated at the file and command boundary, not across every
agent host. Vendor adapters remain intentionally conservative until a stable
public registration contract can be verified.
