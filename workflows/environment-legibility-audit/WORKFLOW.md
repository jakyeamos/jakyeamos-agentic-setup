# Environment legibility audit

Use this workflow when a user wants to audit repositories for machine-legible
architecture, commands, safety constraints, quality gates, or context routing.
It produces evidence and remediation plans; it does not silently remediate a
repository.

## Boundary

1. Require an explicit bounded repository root.
2. Discover repository identities and registered linked worktrees.
3. Group duplicate clones by normalized remote and linked worktrees by their
   common Git directory.
4. Preserve every checkout's path, branch, baseline, dirty state, and
   prunable/unverifiable status as evidence.
5. Exclude private runtime stores, credentials, transcripts, and unrelated
   home-directory paths.

Do not use AIOS or another private session database as audit truth. Do not
contact model providers, deploy, merge, push, install, or alter a target
checkout during the audit.

## Evidence pass

For each repository identity, inspect only bounded files and record provenance:

- architecture and boundaries;
- build, test, lint, and quality commands;
- coding conventions;
- security and credential constraints;
- common failure modes;
- examples of good implementations;
- definition of done and acceptance criteria;
- forbidden or approval-gated paths;
- deployment and rollback;
- context routing and minimum-context behavior.

Validate links and command references where possible. Presence alone earns no
credit. Missing or stale evidence is `unknown`, `stale`, or `blocked`, never an
optimistic pass. Use evidence-backed `N/A` only when the repository class makes
a dimension inapplicable.

When an audit informs a change, map confirmed, inferred, unknown, stale, and
excluded downstream surfaces separately. Each edge needs evidence, confidence,
freshness, provenance, and a declared cap. Zero matches mean no supported
evidence, not no consumers. Keep the map advisory and do not edit consumers
automatically; use the [evidence-backed change-surface workflow](../../skills/evidence-backed-change-surface-mapping/SKILL.md)
for the detailed contract.

## Scoring

Score each applicable dimension from 0 to 4:

- `0` absent;
- `1` present but scattered or informal;
- `2` discoverable but unverified or stale;
- `3` executable and currently validated;
- `4` maintained, routed, and automatically checked.

Separate observations from inferences. For every score, retain the evidence
reference, confidence, freshness, and unresolved question. A repository is at
full potential only when every applicable dimension is level 4.

## Dynamic verification

Run dynamic checks only when a clean, attached, current, non-prunable,
verifiable baseline exists. Materialize that protected revision into a fresh
runtime-owned disposable worktree or archive. Allow only explicitly
allowlisted, non-mutating quality commands; reject shell composition and any
command involving network, install, migration, deploy, merge, push, release,
secrets, deletion, or destructive state changes. Record command hashes and
statuses without storing raw output in public artifacts.

Dependency bootstrap is part of the evidence contract. The disposable
environment must declare whether its tools and dependencies are already
available without network access. Classify results explicitly:

- `pass`: the command ran and exited successfully;
- `fail`: the command ran in an available environment and exited unsuccessfully;
- `blocked`: verification was prevented by policy, including a package manager
  or runner attempting network bootstrap;
- `unavailable`: the executable or required local dependency was not present.

`blocked` and `unavailable` are measurement gaps, not quality failures. Record
only a fixed reason code and an output hash; never persist raw command output in
shared or public artifacts. A no-network command that cannot materialize its
environment must not be reported as a failing repository quality gate.

If the baseline is unsafe or the command cannot be verified, produce a blocked
finding and a remediation step. Do not repair the checkout as part of the
audit.

## Remediation output

Create one directly implementable plan per identity. Each plan names the gap,
evidence, impact, confidence, affected surfaces, P0/P1/P2 tasks, dependencies,
owner, validation commands, acceptance criteria, rollback or removal condition,
and unresolved questions.

For active repositories, propose a small local router and context-index patch
only when the evidence shows a real routing gap. Keep those files short and
reviewable. Dirty, archival, empty, and private-runtime repositories receive a
central plan unless a human explicitly approves a local change.

## Prevention loop

Promote a recurring high-impact failure to a shared rule only when it has a
named owner, executable validation, supported targets, and a removal condition.
Group adjacent symptoms into one routed workflow. Keep global instructions to
hard invariants and pointers; keep procedures here or in a narrow reference.

The current promoted rule is **offline bootstrap classification**:

- Owner: the leverage runtime maintainers.
- Validation: the dynamic audit fixture must distinguish `pass`, `fail`,
  `blocked`, and `unavailable` without retaining raw output; replay must remain
  deterministic.
- Supported targets: any repository with an allowlisted quality command and a
  disposable protected baseline.
- Removal condition: retire the rule only after three consecutive weekly audits
  across at least three repository classes show no misclassified bootstrap
  failures and every dynamic adapter records the same outcome taxonomy.

## Validation

Replay the same ledger with a fixed `as-of` timestamp and require identical
inventory, findings, plans, and summary hashes. Confirm the original checkout
statuses are unchanged. Public exports must contain only validated aggregates
and methodology metadata and require manual review before publication.
