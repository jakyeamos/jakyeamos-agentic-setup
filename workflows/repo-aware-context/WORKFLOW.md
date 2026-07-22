# Repo-aware context routing

Use this workflow before an agent searches broadly, edits a repository, or
recommends an installation.

## Route

1. Identify the exact repository and branch in scope.
2. Resolve the repository identity before broad discovery: normalize its
   remote when present, record its common Git directory, and distinguish each
   checkout or linked worktree state.
3. Read the nearest operating instructions and local context index.
4. Read the live truth file if one exists; treat it as a snapshot, not a
   historical log.
5. Search for an existing implementation before adding a helper or surface.
6. Select only the context needed for the current task.
7. State assumptions when a missing artifact could change the design.

## Identity and freshness gate

Treat repository identity and checkout identity as different records. A
repository identity is grouped by normalized remote when one exists, then by
common Git directory; a repository without a remote uses its bounded path and
declared project identity. A checkout identity records its path, branch, HEAD,
linked-worktree state, and whether the baseline is dirty, detached, stale,
prunable, or unverifiable. Do not collapse those states into one project
status.

Before broad discovery, record the explicit scope and identity evidence. Before
dynamic execution, require a clean, attached, current, non-prunable,
verifiable checkout and materialize that revision in a runtime-owned disposable
worktree. If the source state is unsafe, preserve it and report `blocked`;
never repair, reset, stash, fetch, or improvise in the primary checkout.

For global or low-always-loaded instruction changes, use a report-first route:
inventory loaded surfaces, layering and precedence, duplicates or conflicts,
and ownership before proposing edits. Leave unresolved sources untouched, and
require manifest, drift, or doctor evidence before apply with no-overwrite
behavior. See the [low-always-loaded instruction migration skill](../../skills/low-always-loaded-instruction-migration/SKILL.md).

## Environment evidence

When auditing or preparing a repository, check the context index, linked local
documents, command references, and their freshness. A file's presence is not
evidence that an instruction is routed, executable, or current. A context
index is fresh only when its links resolve, its referenced truth and command
surfaces are current enough for the task, and its provenance can be inspected.
Record broken links, missing owners, stale commands, and unverifiable baselines
explicitly. Use `unknown`, `stale`, or `blocked` when evidence is incomplete;
do not silently fall back to an older packet or an unverified command.

Dynamic command checks must run only from a runtime-owned disposable baseline.
Refuse dirty, detached, stale, prunable, or otherwise unverifiable checkouts,
and compare the original checkout status before and after the check.

## Context layers

Keep these layers separate:

- **Policy:** instructions that govern the agent.
- **Truth:** current branch, status, tests, blockers, and next action.
- **Reference:** stable architecture, contracts, and examples.
- **Evidence:** command output, test results, and review findings.
- **Handoff:** the compact state needed by the next agent or session.

Do not treat a generated index, an old report, or the mere presence of a file
as proof that the behavior is current. Verify behavior at the narrowest useful
surface.

## Minimum-context gate

Load the nearest operating instructions and context index first, then the live
truth needed for the task, then only the routed reference or evidence packets
that the index names. Prefer an architecture map, file pointers, command
references, and targeted search tools over dumping the whole repository into a
context window. Keep policy, truth, reference, evidence, and handoff layers
distinct so an old report cannot masquerade as current state.

If the index is missing, stale, or has broken links, continue with read-only
inspection only when the task permits it and label the context gap. Dynamic
execution, routing decisions, and promotion decisions require the gap to be
resolved or explicitly approved.

For a changed-scope Pre-CR adapter, apply the same gate to context-sensitive
files before a commit: require a local index, validate its links, and preserve
`blocked` for missing or stale evidence. This fast check supplements the deep
leverage audit; it does not replace protected-baseline verification.

## Scope guard

Do not scan a home directory or a multi-repository workspace by default. Ask
for an explicit boundary or use the repository's declared source map. Public
catalogs should contain logical source references rather than machine paths.

The [governed work loop](../governed-work-loop/WORKFLOW.md) is the execution
companion to this routing discipline. The [context-routing case study](../../docs/case-studies/context-routing.md)
records what is observed, what is inferred, and what remains unmeasured.
