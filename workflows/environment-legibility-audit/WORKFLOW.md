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
- `timeout`: an available allowlisted command started but exceeded its declared
  execution limit.

`blocked` and `unavailable` are measurement gaps, not quality failures.
`timeout` is a genuine execution outcome and must be reported separately from
bootstrap failure. Record only a fixed reason code and an output hash; never
persist raw command output in shared or public artifacts. A no-network command
that cannot materialize its environment must not be reported as a failing
repository quality gate.

If the baseline is unsafe or the command cannot be verified, produce a blocked
finding and a remediation step. Do not repair the checkout as part of the
audit. Capture the source checkout status before and after discovery and
preparation; any difference is a failed audit invariant, not a successful
preparation.

## Remediation output

Create one directly implementable plan per identity. Each plan names the gap,
evidence, impact, confidence, affected surfaces, P0/P1/P2 tasks, dependencies,
owner, validation commands, acceptance criteria, rollback or removal condition,
and unresolved questions.

For active repositories, propose a small local router and context-index patch
only when the evidence shows a real routing gap. Keep those files short and
reviewable. Dirty, archival, empty, and private-runtime repositories receive a
central plan unless a human explicitly approves a local change.

## Shared prevention contracts

The audit promotes recurring high-impact failures as a small set of owned
contracts. Each contract has executable validation, supported targets, and a
removal condition. Adjacent documentation symptoms remain grouped in a routed
workflow instead of becoming one rule per symptom.

### `missing-context-index`

- Owner: `repo-aware-context` maintainers.
- Validation: `python3 scripts/validate_prevention_pack.py`, catalog and public
  safety checks, plus deterministic audit replay when the leverage runtime is
  available.
- Supported targets: `generic`, `codex`, `claude`, `cursor`, `copilot`,
  `gemini`, and `antigravity` instruction surfaces.
- Removal condition: retire the promotion only after three consecutive weekly
  audits across at least three repository classes show no missing or stale
  indexes with broken links; keep the hard invariant until then.

### `missing-approval-path-contract`

- Owner: `safe-tool-guards` maintainers.
- Validation: `python3 scripts/validate_prevention_pack.py`, safety scanning,
  and guard fixtures covering exact targets, dry-runs, approval-gated paths,
  and preserved source status.
- Supported targets: `generic`, `codex`, `claude`, `cursor`, `copilot`,
  `gemini`, and `antigravity` tool surfaces.
- Removal condition: retire the promotion only after three consecutive weekly
  audits across at least three repository classes show no unexplained
  approval-gated paths and all applicable repositories expose executable
  checks.

### `missing-security-contract`

- Owner: `safe-tool-guards` maintainers.
- Validation: `python3 scripts/validate_prevention_pack.py`, public-safety and
  redaction checks, and fixtures for credential-bearing arguments, private
  artifacts, network policy, and public projection filtering.
- Supported targets: `generic`, `codex`, `claude`, `cursor`, `copilot`,
  `gemini`, and `antigravity` tool surfaces.
- Removal condition: retire the promotion only after three consecutive weekly
  audits across at least three repository classes show no credential,
  network-boundary, or redaction findings and all public-safety checks pass.

### `unverified-quality-commands`

- Owner: `environment-legibility-audit` maintainers.
- Validation: dynamic fixtures distinguish `pass`, `fail`, `blocked`,
  `unavailable`, and `timeout` without retaining raw output; replay with a
  fixed `as-of` timestamp remains deterministic.
- Supported targets: any repository with an allowlisted quality command and a
  clean, attached, current, non-prunable, verifiable disposable baseline.
- Removal condition: retire the promotion only after three consecutive weekly
  audits across at least three repository classes show no classification drift
  and every dynamic adapter records the same outcome taxonomy.

Promotion requires recurrence, impact, evidence references, and a maintainer
who accepts the removal condition. Do not promote a single co-occurrence or
change-surface inference. Keep global instructions limited to hard invariants
and pointers; keep procedures in this workflow or a narrow reference. Missing,
stale, or blocked evidence must remain visible in routing and promotion
outputs.

## Host integration surfaces

Use three complementary owners rather than turning the audit into another
monolith:

- **Pre-CR** is the fast changed-scope gate. It checks changed files for
  context-routing and public-projection violations, then returns `pass`,
  `fail`, or `blocked`. It must not run providers, network operations,
  migrations, deployments, or writes.
- **Quality Runner** is the source of truth for repository quality gates,
  findings, and review rubrics. Add an environment-legibility skill only after
  candidate ingest, corpus classification, overlap review, and explicit
  activation approval. The audit must consume versioned evidence rather than
  importing the Quality Runner database or creating a second quality engine.
- **Leverage runtime** owns the deep weekly audit, protected disposable
  baselines, repository identity, remediation plans, scorecards, and portfolio
  projections. It may read Quality Runner artifacts but does not repair a
  target checkout.

The Pre-CR adapter is intentionally narrower than the weekly audit. A missing
or stale context index can block a context-sensitive change, while an existing
baseline problem remains a deep-audit finding until the runtime can inspect a
protected disposable revision. Host registration and hook installation remain
manual-review actions.

## Validation

Replay the same ledger with a fixed `as-of` timestamp and require identical
inventory, findings, plans, and summary hashes. Confirm the original checkout
statuses are unchanged. Public exports must contain only validated aggregates
and methodology metadata; they must exclude prompts, code, diffs, paths,
transcripts, credentials, and raw command output and require manual review
before publication. Run `python3 scripts/validate_prevention_pack.py` alongside
the catalog, public-safety, unit, and workbench checks before promoting a change.
